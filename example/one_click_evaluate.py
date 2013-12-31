import fakesysujwxt as jwxt
import json
import sys

def one_click_evaluate(cookie):
    evaluate = jwxt.get_evaluate_list(cookie)
    if evaluate[0] is True:
        evaluate = json.loads(jwxt.format_to_json(evaluate[1]))
    else:
        return (False, 'fail to get course list!')
    courses = evaluate['body']['dataStores']['pj1Stroe']['rowSet']['primary']
    for course in courses:
        course_id = course['resourceid']
        try:
            question_type = course['khtxbh']
        except:
            question_type = course['j']
        questions = jwxt.get_question_list(cookie, question_type)
        question_list = []
        if questions[0] is True:
            questions = json.loads(jwxt.format_to_json(questions[1]))
            questions = questions['body']['dataStores']['wjStroe']['rowSet']['primary']
        else:
            return (False,
                    'fail to get question list on course %s!' % course_id)
        for question in questions:
            question_id = question['resourceId']
            if question is questions[-1]:
                question_list.append([question_id, None])
                break
            options = jwxt.get_option_list(cookie, question['resourceId'])
            if options[0] is True:
                options = json.loads(jwxt.format_to_json(options[1]))
            else:
                return (False,
                        'fail to get option list on question %s!' % question_id)
            option_id = options['body']['dataStores']['qzStore']['rowSet']['primary'][0]['resourceid']
            question_list.append([question_id, option_id])
        course_ooxx_code = jwxt.get_course_ooxx_code(cookie, \
                course['jsbh'], course['kch'], course['khlx'], \
                course['jxbh'], course['khtxbh'], course['pjlx'])
        if course_ooxx_code[0] is True:
            course_ooxx_code = json.loads(jwxt.format_to_json(course_ooxx_code[1]))
            course_ooxx_code = course_ooxx_code['body']['parameters']['bjid']
        else:
            return (False, 'fail to get ooxx_code on course %s!' % course_id)
        result = jwxt.submit_evaluation(cookie, question_list, course_ooxx_code)

if __name__ == "__main__":
    _, cookie = jwxt.login(sys.argv[1], sys.argv[2])
    one_click_evaluate(cookie)
