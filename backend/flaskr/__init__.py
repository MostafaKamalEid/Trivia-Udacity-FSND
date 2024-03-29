import os
from flask import Flask, request, abort, jsonify,request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app,"postgresql://postgres:root@localhost:5432/Trivia")
  

  CORS(app, resources={r"/api/*": {"origins": "*"}})


  def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response


  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories',methods=['GET'])
  def categories():
    categories = Category.query.order_by(Category.id).all()

    if len(categories) == 0:
            abort(404)

    formated_categories = {}
    for category in categories:
        formated_categories[str(category.id)] = str(category.type)

    return jsonify({
      "success" : True,
      "categories": formated_categories,
    })         

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route("/questions",methods=['GET'])
  def retrieve_questions():
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)
    
    if len(current_questions) == 0:
          abort(404)

    categories = Category.query.order_by(Category.type).all()


    return jsonify({
      "success" : True,
      "questions": current_questions,
      "total questions" : len(questions),
      "current category": None,
      "categories": {category.id: category.type for category in categories}
    })         


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route("/questions/<question_id>",methods=['DELETE'])
  def delete_question(question_id):
      try:
        question = Question.query.filter_by(id=question_id).first()
        question.delete()
        return jsonify({
          "success":True
        })
      except :
        abort(422)
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route("/questions",methods=['POST'])
  def add_question():
        
      body = request.get_json()
      question = body.get('question')
      answer = body.get('answer')
      difficulty = body.get('difficulty')
      category = body.get('category')
      if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
            abort(422)
      try:
          question = Question(question=question, answer=answer,
                                difficulty=difficulty, category=category)
          question.insert()

          return jsonify({
                'success': True,
                'created': question.id,
            })

      except:
            abort(422)


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route("/questions/search",methods=['POST'])
  def search_question():
        body = request.get_json()
        search = body.get('searchTerm', None)
        if search is None:
              abort(422)
        try:
            results = Question.query.filter(
                Question.question.ilike(f'%{search}%')).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in results],
                'total_questions': len(results),
                'current_category': None
            })
        except : 
          abort(422)


  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route("/categories/<int:category_id>/questions",methods=['GET'])
  def retrieve_questions_by_category(category_id):
        
    try:
        questions = Question.query.filter_by(category=str(category_id)).all()

        return jsonify({
            'success': True,
            'questions': [question.format() for question in questions],
            'total_questions': len(questions),
            'current_category': category_id
            })
    except:
            abort(404)
  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route("/quizzes",methods=['POST'])
  def play():
        try:

            body = request.get_json()

            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((previous_questions))).all()

            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(422)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422
  @app.errorhandler(500)
  def unprocessable(error):
      return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500      
  
  return app

    