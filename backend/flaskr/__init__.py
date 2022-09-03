from crypt import methods
import os
from sre_constants import CATEGORY
from tkinter.messagebox import QUESTION
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories")
    def retrieve_all_categories():
        categories = Category.query.order_by(Category.id).all()
        categoriesDict = {}

        for categorie in categories:
            categoriesDict[categorie.id] = categorie.type
        return jsonify (
            {
                "success" : True,
                "categories": categoriesDict,
                "tatal_categories":len(Category.query.all()),
            }
            )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: À ce stade, lorsque vous démarrez l'application
    Vous devriez voir des questions et des catégories générées,
    Dix questions par page et pagination en bas de l'écran pendant trois pages.
    Cliquer sur les numéros de page devrait mettre à jour les questions.
    """
    
    @app.route("/questions")
    def get_questions () :
        try:
            questions =  Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, questions)
            total_question = len(questions)

            if (len(current_question) == 0):
                abort(404)
            categories = Category.query.all()
            categoriesDict = {}
            for categorie in categories:
                categoriesDict[categorie.id] = categorie.type
            
            return jsonify(
                {
                    "success" : True,
                    "questions": current_question,
                    "totalQuestions" : total_question,
                    "categories" : categoriesDict,
                }
            )
        except:
            abort(400)
        
    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:id>", methods=['DELETE'])
    def delete_question(id):
        try:
            questions =  Question.query.filter_by(id=id).one_or_none()
            if questions is None:
                abort(404)
                
            questions.delete()
            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)
            return jsonify (
                {
                    "success": True,
                    "deleted": id,
                    "totalQuestions" :current_question,
                }
            )
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    
    @app.route("/questions", methods=['POST'])
    
    def add_question ():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)
        try:
            question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "created":question.id,
                    "question": current_question,
                    "total_question": len(selection),
                }
            )
        except Exception as e:
            print(e)
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/search", methods=['POST'])
    def search():
        body = request.get_json()
        searchTerm = body.get('searchTerm')
        questions = Question.query.filter(Question.question.ilike('%' + searchTerm + '%')).all()
        if questions:
            current_question = paginate_questions(request, questions)
            return jsonify(
                {
                    "success": True,
                    "questions": current_question,
                    "totalQuestions": len(questions),
                    
                }
            )
        else:
            abort(404)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:id>/questions")
    def questions_in_category(id):
        category = Category.query.filter_by(id=id).one_or_none()
        if category:
            questions_in_cat = Question.query.filter_by(category=str(id)).all()
            current_question = paginate_questions(request, questions_in_cat)
            return jsonify(
                {
                    "success": True,
                    "questions": current_question,
                    "total_questions": len(questions_in_cat),
                    "current_category":category.type
                }
            )
        else:
            abort(404)
    """
    @TODO:
    Créez un point de terminaison post pour obtenir des questions pour jouer au quiz.
    Ce point de terminaison doit prendre la catégorie et les paramètres de question précédents
    et retourner une question aléatoire dans la catégorie donnée,
    Si cela est fourni, et ce n'est pas l'une des questions précédentes.

    Test: dans l'onglet "Play", après qu'un utilisateur sélectionne "tous" ou une catégorie,
    Une question à la fois est affichée, l'utilisateur est autorisé à répondre
    et montré qu'ils étaient corrects ou non.
    """
    @app.route('/quizzes', methods=['POST'])
    def quiz():
        # get the qestion category an the previous question
        body = request.get_json()
        quizCategory = body.get('quiz_category')
        previousQuestion = body.get('previous_questions')

        try:
            if (quizCategory['id'] == 0):
                questionsQuery = Question.query.all()
            else:
                questionsQuery = Question.query.filter_by(category=quizCategory['id']).all()

            randomIndex = random.randint(0, len(questionsQuery)-1)
            nextQuestion = questionsQuery[randomIndex]

            #stillQuestions = True
            while nextQuestion.id not in previousQuestion:
                nextQuestion = questionsQuery[randomIndex]
                return jsonify({
                    'success': True,
                    'question': {
                        "answer": nextQuestion.answer,
                        "category": nextQuestion.category,
                        "difficulty": nextQuestion.difficulty,
                        "id": nextQuestion.id,
                        "question": nextQuestion.question
                    },
                    'previousQuestion': previousQuestion
                })

        except Exception as e:
            print(e)
            abort(404)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "The server has encountered a situation it does not know how to handle !"
        }), 500
    return app

