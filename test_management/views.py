# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .models import Test
# from .forms import TestUpload


# Create your views here.
def test_list(request):
    tests = Test.objects.all()
    return render(request, 'test_list.html', {'tests' : tests})

def subject_list(request):
    return render(request, 'subject_list.html')

def topic_list(request):
    return render(request, 'topic_list.html')
    
def question_list(request):
    return render(request, 'question_list.html')

def import_question(request):
    return render(request, 'import_question.html')

def add_test(request):
    if request.method == 'POST':
        test_name = json.loads(request.POST.get('test_name'))
        test_type = json.loads(request.POST.get('test_type'))
        test_date = json.loads(request.POST.get('test_date'))
        test_date = datetime.strptime(test_date, '%Y-%m-%d').date()
        test_obj = Test(test_name = test_name, test_type = test_type, test_date = test_date)
        test_obj.save()
        return HttpResponseRedirect('/test-management/test/')

def delete_test(request):
    if request.is_ajax():
        selected_tests = request.POST['test_list_ids']
        selected_tests = json.loads(selected_tests)
        for i, test in enumerate(selected_tests):
            Test.objects.filter(id__in=selected_tests).delete()
        return HttpResponseRedirect('/test-management/test/')