# Agentic Workflow

1. User: “I want to sign up for the Machine Learning Bootcamp.”
2. LLM Function Call #1 → Information request (DB lookup):
   • get_course_info(course_name)
   • Returns details: price, start date, available seats.
3. Dependency: Only if seats are available does the system proceed.
4. LLM Function Call #2 → Action initiation:
   • enroll_student(student_id, course_id)
   • Attempts to add the student to the course roster.
5. Exception process:
   • If enrollment fails (e.g., class is full, payment method invalid), trigger a different flow:
   • Suggest an alternative date or course → get_alternative_courses(topic)
   • Or retry with a different payment option.
6. Follow-up Action (dependent):
   • Once enrollment succeeds, trigger a secondary action:
   • send_welcome_email(student_id, course_id)
   • This shows chaining of actions after success.
