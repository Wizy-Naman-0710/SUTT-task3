from django.db import models
from datetime import timedelta
import uuid 
from django.utils.timezone import now

class Student(models.Model): 
    student_uid = models.CharField(max_length=100, unique=True)
    student_name =models.CharField(max_length=100)
    bits_id = models.CharField(max_length=13, unique=True)
    hostel = models.CharField(max_length=7)
    
    def __str__(self):
        return self.student_name
    

class Book(models.Model): 
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=14, unique=True)
    book_cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    def __str__(self):
        return self.title
    

    def borrow_book(self):
        if self.available_copies > 0:
            self.available_copies -= 1
            self.save()
        else:
            raise ValueError("No copies available.")

    def return_book(self):
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save()
        else:
            raise ValueError("All copies are already returned.")
    

def date_estimation(): 
    return now() + timedelta(days=14)


class BorrowRecord(models.Model):
    record_id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrow_date = models.DateTimeField(default=now)
    return_date = models.DateTimeField(default=date_estimation) 
    returned = models.BooleanField(default=False)
    late_fees = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.student} borrowed {self.book}"
    
    def reissue_book(self): 
        self.return_date = models.DateTimeField(default=date_estimation)
    
    def calculate_late_fees(self):
        if not self.returned and now() > self.return_date:
            days_late = (now() - self.return_date).days
            self.late_fees =  days_late * 10
        



class Review(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    review_text = models.TextField()
    rating = models.PositiveSmallIntegerField()  # 1-5 rating
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.student} on {self.book}"
    
    def rating_range(self):
        return range(self.rating)

class FavouriteRecord(models.Model): 
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} has {self.book} as his favourite"
 

class FeedbackRoom(models.Model): 
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    def __str__(self):
        return self.student.student_name

class FeedbackRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    body = models.CharField(max_length=1000)
    date = models.DateTimeField(default=now)
    admin_reply = models.BooleanField(default=False)

    def __str__(self): 
        return f"Student {self.student} has a feedback/complain with subject: {self.subject}"
