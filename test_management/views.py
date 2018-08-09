# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json, csv, logging, ast
from datetime import datetime
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http.response import JsonResponse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from .models import *
from .forms import QuestionForm, OptionForm
from .serializers import QuestionSerializer, OptionSerializer
from register.models import Register
# from .forms import TestUpload


# Create your views here.
def test_list(request):
    tests = Test.objects.all()
    return render(request, 'test_list.html', {'tests' : tests})

def add_test(request):
    if request.method == 'POST':
        test_name = json.loads(request.POST.get('test_name'))
        test_type = json.loads(request.POST.get('test_type'))
        test_date = json.loads(request.POST.get('test_date'))
        test_date = datetime.strptime(test_date, '%Y-%m-%d').date()
        test_obj = Test(test_name = test_name, test_type = test_type, test_date = test_date)
        test_obj.save()
        return HttpResponseRedirect('/test/')

def edit_test(request):
    if request.method == 'POST':
        row_id = json.loads(request.POST.get('row_id'))
        test_name = json.loads(request.POST.get('test_name'))
        test_type = json.loads(request.POST.get('test_type'))
        test_date = json.loads(request.POST.get('test_date'))

        test_date = datetime.strptime(test_date, '%Y-%m-%d').date()
        row_id = int(row_id)
        tests = Test.objects.all()
        
        for test_obj in tests:
            if test_obj.id == row_id:
                test_obj.test_name = test_name
                test_obj.test_type = test_type
                test_obj.test_date = test_date
                test_obj.save()
                return HttpResponseRedirect('/test/')

def delete_test(request):
    if request.is_ajax():
        selected_tests = request.POST['test_list_ids']
        selected_tests = json.loads(selected_tests)
        for i, test in enumerate(selected_tests):
            Test.objects.filter(id__in=selected_tests).delete()
        return HttpResponseRedirect('/test/')
    
def question_list(request):
    questions = Question.objects.all()
    questionForm = QuestionForm()
    optionForm = OptionForm()
    return render(request, 'question_list.html', {'questions' : questions, 'questionForm' : questionForm, 'optionForm' : optionForm })

def add_question(request):
    if request.method == 'POST':
        question_name = json.loads(request.POST.get('question_name'))
        question_type = json.loads(request.POST.get('question_type'))
        test_id = json.loads(request.POST.get('test_id'))
        question_obj = Question(question_name = question_name, question_type = question_type, test_id = Test.objects.get(id=test_id))
        question_obj.save()
        
        option_rows = json.loads(request.POST.get('option_rows'))
        for option in option_rows:
            option_obj = Option()
            option_obj.question_id = question_obj
            option_obj.option_name = option
            option_obj.answer = option_rows[option]
            option_obj.save()
        return HttpResponseRedirect('/question/')

def edit_question(request):
    context = dict()
    if request.method == 'GET':
        row_id = request.GET.get('row_id')
        question_obj = Question()
        question = question_obj.edit_question(row_id)
        question_form = QuestionForm(initial={'question_name': question[0]['question_name'],
                                            'question_type': question[0]['question_type'],
                                            'test_id': question[0]['test_id']}, auto_id=False).__str__()
        option_form = ""
        if question[1]:
            cont = dict()
            options_form = []
            for option in question[1]:
                option_form = OptionForm(initial={'option_name': option['option_name'],
                                                    'answer': option['answer']})
                options_form.append(option_form)
            cont.update({'options': options_form})
            option_form = render_to_string('include/question_option_row.html', cont)
        context.update({
            'question_form': question_form,
            'option_form': option_form,
        })          
        return JsonResponse(context)
    elif request.method == 'POST':
        row_id = json.loads(request.POST.get('row_id'))
        test_id = json.loads(request.POST.get('test_id'))
        question_type = json.loads(request.POST.get('question_type'))
        question_name = json.loads(request.POST.get('question_name'))
        option_rows = json.loads(request.POST.get('option_rows'))
        kwargs = {"test_id":test_id, "question_type":question_type, "question_name":question_name, "option_rows":option_rows}
        question_obj = Question()
        question = question_obj.edit_question_save(row_id, **kwargs)
        return HttpResponseRedirect('/question/')

def delete_question(request):
    if request.is_ajax():
        selected_questions = request.POST['question_list_ids']
        selected_questions = json.loads(selected_questions)
        for i, test in enumerate(selected_questions):
            Question.objects.filter(id__in=selected_questions).delete()
        return HttpResponseRedirect('/question/')

def import_question(request):
    if request.method == 'GET':
        with open('static/sample/import_question_sample.csv', 'rb') as csv_file:
            response = HttpResponse(csv_file.read())
            csv_file.close()
            response['content_type'] ='text/csv'
            response['Content-Disposition'] = 'attachment; filename="import_question_sample.csv"'
            print response
            return response
    elif request.method == 'POST':
        # if not GET, then proceed
        try:
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                messages.error(request,'File is not CSV type')
                return None
                # return HttpResponseRedirect(reverse("myapp:upload_csv"))
            #if file is too large, return
            if csv_file.multiple_chunks():
                messages.error(request,"Uploaded file is too big (%.2f MB)." % (csv_file.size/(1000*1000),))
                return None
                # return HttpResponseRedirect(reverse("myapp:upload_csv"))
            csv_file.open()
            file_data = csv_file.read().decode("utf-8")
            data_lines = file_data.split("\n")
            last_test_id = None
            last_question_id = None  

            for line in range(1, len(data_lines)):
                fields = data_lines[line].split(",")

                test_id = fields[0]
                test_name = fields[1]
                test_type = fields[2]
                test_date = fields[3]
                question_type = fields[4]
                question_name = fields[5]
                option = fields[6]
                answer = fields[7]

                test_context = {
                    "test_name": test_name,
                    "test_type": test_type,
                    "test_date": test_date
                }
                question_context = {
                    "question_type": question_type,
                    "question_name": question_name,
                    "option": option,
                    "answer": answer
                }
                           
                if not test_id:
                    if not(test_name and test_type and test_date):
                        if not(question_type and question_name):
                            #if `question` fields are empty, add option of the same question
                            question_id = last_question_id
                            Option().add_option(question_id, **question_context)
                        #if `test` fields are empty, add question of the same test
                        else:   
                            test_id = last_test_id
                            Question().add_question(test_id, **question_context)
                    #if `test_id` field is empty, add new test
                    else:
                        test = Test()
                        test_id = test.add_test(**test_context)
                        question_id = Question().add_question(test_id, **question_context)
                        last_test_id = test_id
                        last_question_id = question_id
                #`test_id` field has value, check if value match any `Test` object
                else:
                    try:
                        test_obj = Test.objects.get(id = test_id)
                    except:
                        test_obj = None
                    if test_obj:
                        question_id = Question().add_question(test_id, **question_context)
                        last_test_id = test_id
                        last_question_id = question_id
                    #`test_id` field has value, not in any `Test` object
                    else:
                        test = Test()
                        test_id = test.add_test(**test_context)
                        question_id = Question().add_question(test_id, **question_context)
                        last_test_id = test_id
                        last_question_id = question_id
                        

        except Exception as e:
                messages.error(request,"Unable to upload file. "+repr(e))
            
        return HttpResponseRedirect('/question/')
    return HttpResponse('/question/')

@csrf_exempt
def get_question_lists(request):
    """
    API to get a list of questions
    """
    if request.method == 'GET':
        credential = ast.literal_eval(request.body)
        email = credential['email']
        password = credential['password']
        status = Register().login_authentication(email, password)
        if status is True:
            # Adapt logic to how many questions should retrieve each time
            questions = Question.objects.all()
            question_id = list()
            for question in questions:
                if question.question_type == 'QCM':
                    if Option.objects.filter(question_id = question.id):
                        question_id.append(question.id)
            options = Option.objects.filter(question_id__in = question_id)
            option_serializer = OptionSerializer(options, many = True)
            print option_serializer
            question_serializer = QuestionSerializer(questions, many = True)
            context = {
                "status": "200",
                "message": "Success",
                "question" : question_serializer.data,
                "option" : option_serializer.data,
            }
            messages.add_message(request, messages.SUCCESS, "Succesfully login!")
            return JsonResponse(context, safe=False)
        context = {
            "status": "500",
            "message": "Error"
        }
        return JsonResponse(context, safe=False)
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = QuestionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
