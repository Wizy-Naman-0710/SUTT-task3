from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from .models import *
from allauth.socialaccount.models import SocialAccount
import requests
import os 
from django.http import FileResponse
from fuzzywuzzy import process
from django.conf import settings
import pandas as pd
from django.core.files import File

def get_student(request): 
    social_account = SocialAccount.objects.get(user=request.user, provider='google')
    google_uid = social_account.uid
    student = Student.objects.get(student_uid=google_uid)

    return student

def signIn(request): 
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('admin_dashboard/')  
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'sign-in.html')

def logout_views(request): 
    logout(request)
    return redirect('/')


def is_not_staff(user):
    return not user.is_staff


@user_passes_test(is_not_staff, login_url='')
@login_required
def google_login(request): 

    if request.user.is_authenticated:
        try: 
            social_account = SocialAccount.objects.get(user=request.user, provider='google')
            google_uid = social_account.uid
            if Student.objects.filter(student_uid=google_uid).exists():
                return redirect('users:student_dashboard')
            else: 
                student = Student.objects.create(
                    student_uid = google_uid, 
                    student_name = social_account.extra_data.get('name'), 
                )
                student.save()
                return redirect('users:student_info')
        except SocialAccount.DoesNotExist: 
            return "No Google account linked."

    return redirect('users:student_dashboard')



@user_passes_test(is_not_staff, login_url='')
@login_required
def student_info(request): 
    student = get_student(request)

    if request.method == 'POST': 
        student.bits_id = request.POST['bits-id']
        student.hostel = request.POST['hostel']
        student.save()
            
        return redirect('users:student_dashboard')
    
    return render(
        request, 
        'student_info.html', 
        {
            'bits_id' : student.bits_id,
            'hostel' : student.hostel, 
        },
    )


#All student views 
@user_passes_test(is_not_staff, login_url='')
@login_required
def student_dashboard(request): 
    student = get_student(request)
    current_books = BorrowRecord.objects.all().filter(student=student, returned=False)
    total_fees = 0

    for book in current_books: 
        total_fees += book.late_fees

    return render(
        request,
        'student_dashboard.html',
        {
            'student' : student,
            'current_books' : current_books.count(), 
            'total_fees' : total_fees,
            'records' : BorrowRecord.objects.filter(student=student, returned = False)
        },
    )
    
@user_passes_test(is_not_staff, login_url='')
@login_required
def student_book_details(request, book_isbn): 

    student = get_student(request)
    book = get_object_or_404(Book , isbn=book_isbn)

    added_favourite = False 
    borrowed = False 
    borrowed_before = False 

    if FavouriteRecord.objects.filter(student=student, book=book).exists():
        added_favourite = True 

    if BorrowRecord.objects.filter(student=student, book=book, returned=False).exists(): 
        borrowed = True 

    if BorrowRecord.objects.filter(student=student, book=book).exists(): 
        borrowed_before = True

    if request.method == 'POST':
        review = Review.objects.create(
            student = student, 
            book = book, 
            review_text = request.POST['review_text'],
            rating = request.POST['rating'],
        )

        review.save()

    import math

    reviews = Review.objects.filter(book=book)
    sum = 0 
    
    for review in reviews: 
        sum += review.rating

    # to avoid division by zero error, we are using try-except
    try : 
        average = sum / reviews.count()
    except: 
        average = 0

    average_range = range(int(math.floor(average)))

    return render(
        request,
        'student_book_details.html', 
        {
            'book' : book,
            'is_borrowed': borrowed, 
            'added_favourite': added_favourite,
            'borrowed_before' : borrowed_before,
            'reviews' : reviews,
            'average_rating' : average, 
            'average_range': average_range, 
        }
    )



@user_passes_test(is_not_staff, login_url='')
@login_required
def borrow_book(request, book_isbn): 
    student = get_student(request)
    book = get_object_or_404(Book, isbn=book_isbn)
    book.borrow_book()

    record = BorrowRecord.objects.create(
        student = student, 
        book = book
    )
    record.save() 
    return redirect('users:student_dashboard')

@user_passes_test(is_not_staff, login_url='')
@login_required
def return_book(request, record_id): 
    record = get_object_or_404(BorrowRecord, record_id=record_id)
    record.book.return_book()
    record.returned = True 
    record.return_date = now()
    record.save()

    return redirect('users:student_dashboard')

@user_passes_test(is_not_staff, login_url='')
@login_required
def reissue_book(request, record_id): 
    record = get_object_or_404(BorrowRecord, record_id=record_id)
    record.return_date = now() + timedelta(days=14)
    record.save()

    return redirect('users:student_dashboard')


@user_passes_test(is_not_staff, login_url='')
@login_required
def student_search_books(request): 
    books = Book.objects.all().order_by('-title')
    search_value = ''
    messages = []

    
    if request.method == 'POST':
        search_value = request.POST.get('search', '').strip()
        search_by = request.POST.get('search-by', '')
        
        if search_value:
            if search_by == 'title':

                titles = books.values_list('title', flat=True)
                best_matches = process.extract(search_value, titles, limit=5)
                
                matched_titles = [match[0] for match in best_matches]
                books = [Book.objects.get(title=title) for title in matched_titles]

                if int(best_matches[0][1]) > 70 and int(int(best_matches[0][1]) < 99): 
                    messages.append(f'Did you mean: {best_matches[0][0]}')

                

            elif search_by == 'isbn':
                books = books.filter(isbn=search_value)
                if len(books) == 0: 
                    messages.append('No books found')

    return render(
        request,
        'student_search_books.html',
        {
            'books': books,
            'search_value': search_value,
            'messages': messages
        }
    )



@user_passes_test(is_not_staff, login_url='')
@login_required
def student_history(request): 
    student = get_student(request)
    records = BorrowRecord.objects.filter(student=student, returned = True).order_by('-return_date')
    return render(request, 'student_history.html', {'records' : records})


@user_passes_test(is_not_staff, login_url='')
@login_required
def add_favourite(request, book_isbn): 
    student = get_student(request)
    book = get_object_or_404(Book, isbn=book_isbn)

    if FavouriteRecord.objects.filter(student=student, book=book).exists():
        return redirect('users:student_favourites')

    favourite = FavouriteRecord.objects.create(student=student, book=book)
    favourite.save()

    return redirect('users:student_favourites')


@user_passes_test(is_not_staff, login_url='')
@login_required
def remove_favourite(request, book_isbn): 
    student = get_student(request)
    book = get_object_or_404(Book, isbn=book_isbn)

    favourite = get_object_or_404(FavouriteRecord, student=student, book=book)
    favourite.delete()
    return redirect('users:student_favourites')


@user_passes_test(is_not_staff, login_url='')
@login_required
def student_feedback(request): 
    student = get_student(request) 
    if request.method == 'POST': 
        if not FeedbackRoom.objects.filter(student=student).exists(): 
            room = FeedbackRoom.objects.create(student=student)
            room.save()

        feedback = FeedbackRecord.objects.create(
            student = student, 
            subject = request.POST['subject'],
            body = request.POST['body'],
        )
        feedback.save()
        return redirect('users:student_feedback')
    
    feedbacks = FeedbackRecord.objects.filter(student=student )
    return render(request, 'student_feedback.html', {'feedbacks' : feedbacks })


@user_passes_test(is_not_staff, login_url='')
@login_required
def student_favourites(request):
    student = get_student(request)
    favourites = FavouriteRecord.objects.filter(student=student)
    return render(request, 'student_favourites.html', {'favourites': favourites})


#all admin views 
@staff_member_required(login_url='')
@login_required
def admin_dashboard(request): 
    total_books = Book.objects.all().count()
    borrowed_books = BorrowRecord.objects.filter(returned= False).count()
    return render(
        request,
        'admin_dashboard.html', 
        {
            'user_name' : request.user,
            'total_books' : total_books, 
            'borrowed_books': borrowed_books}
        )


#the autofill function to the details of the books
def get_book_info(isbn):
    url = f"https://openlibrary.org/api/books"
    params = {
        'bibkeys': f'ISBN:{isbn}',
        'format': 'json',
        'jscmd': 'data'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()

        if f'ISBN:{isbn}' in data:
            book = data[f'ISBN:{isbn}']
            title = book.get('title', 'N/A')
            authors = ', '.join([author['name'] for author in book.get('authors', [])])
            cover_image = book.get('cover', {}).get('medium', 'No cover image available')
            print(cover_image)
            return {
                'book_isbn' : isbn, 
                'book_name' : title, 
                'book_author': authors, 
                'book_image' : cover_image
            }
        else:
            print("No book found with the provided ISBN.")
    else:
        print(f"Error: Unable to fetch data (Status code: {response.status_code})")


@staff_member_required(login_url='')
@login_required
def add_book_info(request): 
    if request.method == 'POST': 
        book_info = get_book_info(request.POST['book_isbn'])
        return render(request, 'admin_add_books.html', book_info)
    

@staff_member_required(login_url='')
@login_required
def admin_add_books(request): 
    messages = [] 
    if request.method == 'POST': 
        action = request.POST.get('action') 
        if action=='autofill': 
            book_info = get_book_info(request.POST['book_isbn'])
            return render(request, 'admin_add_books.html', book_info)

        if action=='add_book_list': 
            def_messages = booklist_excel(request.FILES['book_list'])
            print(def_messages)
            return render(request, 'admin_add_books.html', {'messages' : def_messages})
            

        if action=='save': 
            if Book.objects.filter(isbn = request.POST['book_isbn']).exists() : 
                messages.append("Book with same ISBN already exist")
                return render(request, 'admin_add_books.html', {'messages' : messages})
            
            print(request.FILES)
            print("i am doing something")
            book = Book.objects.create(
                isbn = request.POST['book_isbn'], 
                title = request.POST['book_name'], 
                author = request.POST['book_author'], 
                total_copies = request.POST['total_copies'],
                available_copies = request.POST['total_copies'],
                book_cover_image=request.FILES.get('book_cover_image'),
            )

            book.save()
            return redirect('users:admin_book_details', book_isbn = request.POST['book_isbn'])
            
        
    return render(request, 'admin_add_books.html', {'messages' : messages})


def booklist_excel(filepath): 
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip()
    messages = []
    required_columns = ['ISBN-13', 'Title', 'Author', 'Cover', 'Copies']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError
           
        
    for _, row in df.iterrows():
        if pd.isnull(row['ISBN-13']) or pd.isnull(row['Title']) or pd.isnull(row['Author']) or pd.isnull(row['Copies']):
            messages.append(f"Skipping row due to missing required fields: {row}")
            continue

        if Book.objects.filter(isbn=row['ISBN-13']).exists():
            messages.append(f"Skipping row because ISBN-13 already exists: {row['ISBN-13']}")
            continue

        # Create the Book instance
        print('doing something')
        try:
            book = Book(
                title=row['Title'],
                author=row['Author'],
                isbn=row['ISBN-13'],
                total_copies=row['Copies'],
                available_copies=row['Copies'],  # Initial available copies match total copies
            )

            if not pd.isnull(row['Cover']):
                cover_image_path = row['Cover']  
                full_image_path = os.path.join(settings.MEDIA_ROOT, 'book_covers', os.path.basename(cover_image_path))
                if os.path.exists(full_image_path):
                    with open(full_image_path, 'rb') as image_file:
                        book.book_cover_image.save(os.path.basename(full_image_path), File(image_file))
                else:
                    messages.append(f"Image file not found: {full_image_path}, skipping cover image.")

    
            book.full_clean()  #check for full validation
            book.save()
            messages.append(f"Book added: {book.title} ({book.isbn})")

        except Exception as e:
            messages.append(f"Error while adding book: {row}, Error: {e}")

    
    return messages

@staff_member_required(login_url='')
@login_required
def admin_edit_book(request): 
    books = Book.objects.all().order_by('-id')
    return render(request, 'admin_edit_book.html', {'books': books})


@staff_member_required(login_url='')
@login_required
def admin_feedback(request): 
    rooms = FeedbackRoom.objects.all()
    return render(request, 'admin_feedback.html', {'rooms': rooms})


@staff_member_required(login_url='')
@login_required
def admin_chat(request, bits_id): 
    rooms = FeedbackRoom.objects.all()
    student = get_object_or_404(Student, bits_id=bits_id)
    feedbacks = FeedbackRecord.objects.filter(student=student)

    if request.method == 'POST': 
        feedback = FeedbackRecord.objects.create(
            student = student, 
            subject = request.POST['subject'],
            body = request.POST['body'],
            admin_reply = True,
        )
        feedback.save()

        return redirect('users:admin_chat', bits_id = bits_id)

    
    return render(
        request, 
        'admin_chat.html', 
        {
            'rooms' : rooms, 
            'feedbacks': feedbacks,
        }
    )


@staff_member_required(login_url='')
@login_required
def admin_book_details(request, book_isbn): 
    book = get_object_or_404(Book, isbn=book_isbn)
    records = BorrowRecord.objects.filter(book=book, returned=False)
    reviews = Review.objects.filter(book=book)
    reviews = Review.objects.filter(book=book)
    sum = 0
    for review in reviews: 
        sum += review.rating
    import math
    try : 
        average = sum / reviews.count()
    except: 
        average = 0

    average_range = range(int(math.floor(average)))

    return render(
        request,
        'admin_book_details.html', 
        {
            'book': book,
            'records' : records,
            'reviews' : reviews,
            'average_rating' : average, 
            'average_range': average_range
        },
    )

def download_excel(request) : 
    print(settings.BASE_DIR)
    file_path = os.path.join(settings.MEDIA_ROOT, 'book_template.xlsx')
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename="booklist_template.xlsx"'
    print('button was clicked')
    print(response)
    return response



@staff_member_required(login_url='')
@login_required
def admin_change_details(request, book_isbn): 
    post = request.POST
    messages = []
    book = get_object_or_404(Book, isbn=book_isbn)
    issued_books = int(book.total_copies) - int(book.available_copies)
    if request.method == 'POST': 
        book.isbn = post['book_isbn'] 
        book.title = post['book_name'] 
        book.author = post['book_author'] 
        book.book_cover_image = post['book_cover_image']
        if issued_books > int(post['total_copies']): 
            messages.append('Book cannot be editied because the new copies is less than issued copies')
            return render(request, 'admin_change_details.html', {'messages' : messages, 'book' : book})
        
        book.total_copies = post['total_copies']
        book.available_copies = int(post['total_copies']) - issued_books
        
        book.save()

        return redirect('users:admin_book_details', book_isbn=book.isbn)
    
    return render(request, 'admin_change_details.html', {'book': book})


@staff_member_required(login_url='')
@login_required
def delete_book(request, book_isbn):
    book = get_object_or_404(Book, isbn=book_isbn)
    book.delete()
    return redirect('users:admin_edit_book')

