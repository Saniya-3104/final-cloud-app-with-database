from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Lesson, Question, Choice, Submission, Enrollment

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.all()

class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'

def enroll(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        Enrollment.objects.get_or_create(user=request.user, course=course)
        return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))

def registration_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.POST['password']
        try:
            User.objects.get(username=username)
            return render(request, 'onlinecourse/registration.html', {'error': 'User already exists'})
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/registration.html')

def login_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            return render(request, 'onlinecourse/login.html', {'error': 'Invalid username or password'})
    return render(request, 'onlinecourse/login.html')

def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')

def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        selected_ids = []
        for key, value in request.POST.items():
            if key.startswith('choice_'):
                selected_ids.append(int(value))
        
        enrollment, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
        submission = Submission.objects.create(enrollment=enrollment)
        
        choices = Choice.objects.filter(id__in=selected_ids)
        submission.choices.set(choices)
        submission.save()
        
        return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)
    return redirect('onlinecourse:course_details', pk=course_id)

def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    total_score = 0
    user_score = 0
    selected_choices = submission.choices.all()
    
    for question in course.question_set.all():
        total_score += question.grade
        correct_choices = set(question.choice_set.filter(is_correct=True))
        user_choices = set(selected_choices.filter(question=question))
        if correct_choices == user_choices and len(correct_choices) > 0:
            user_score += question.grade
            
    grade = int((user_score / total_score) * 100) if total_score > 0 else 0
    
    context = {
        'course': course,
        'submission': submission,
        'grade': grade,
        'selected_ids': [c.id for c in selected_choices]
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
