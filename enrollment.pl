:- dynamic(enrolled/2).

student(s1, 'Sayan Pal', cse).
student(s2, 'Rahul Sharma', cse).
student(s3, 'Priya Das', aiml).
student(s4, 'Amit Kumar', ece).
student(s5, 'Sneha Roy', it).
student(s6, 'Ananya Sen', cse).
student(s7, 'Arjun Mehta', aiml).
student(s8, 'Neha Verma', ece).
student(s9, 'Rohan Gupta', it).
student(s10, 'Ishita Bose', cse).

course(c1, 'Artificial Intelligence', cse).
course(c2, 'Database Management System', cse).
course(c3, 'Computer Networks', cse).
course(c4, 'Machine Learning', aiml).
course(c5, 'Digital Electronics', ece).
course(c6, 'Operating Systems', cse).
course(c7, 'Data Structures and Algorithms', cse).
course(c8, 'Deep Learning', aiml).
course(c9, 'Embedded Systems', ece).
course(c10, 'Web Technologies', it).
course(c11, 'Cloud Computing', it).

credits(c1, 4).
credits(c2, 4).
credits(c3, 4).
credits(c4, 4).
credits(c5, 3).
credits(c6, 4).
credits(c7, 4).
credits(c8, 4).
credits(c9, 3).
credits(c10, 3).
credits(c11, 3).

enrolled(s1, c1).
enrolled(s1, c2).
enrolled(s1, c3).

enrolled(s2, c2).
enrolled(s2, c3).

enrolled(s3, c1).
enrolled(s3, c4).

enrolled(s4, c5).

enrolled(s5, c2).

enrolled(s1, c6).
enrolled(s2, c7).
enrolled(s3, c8).
enrolled(s4, c9).
enrolled(s5, c10).
enrolled(s5, c11).

enrolled(s6, c1).
enrolled(s6, c7).
enrolled(s7, c4).
enrolled(s7, c8).
enrolled(s8, c5).
enrolled(s8, c9).
enrolled(s9, c10).
enrolled(s9, c11).
enrolled(s10, c2).
enrolled(s10, c6).

student_exists(StudentId) :-
    student(StudentId, _, _).

course_exists(CourseId) :-
    course(CourseId, _, _).

department(Department) :-
    student(_, _, Department).
department(Department) :-
    course(_, _, Department).

is_enrolled(Student, Course) :-
    enrolled(Student, Course).

student_courses(Student, Course) :-
    enrolled(Student, Course).

course_students(Course, Student) :-
    enrolled(Student, Course).

student_course_name(Student, CourseName) :-
    enrolled(Student, CourseId),
    course(CourseId, CourseName, _).

students_in_department(Department, Student) :-
    student(Student, _, Department).

courses_in_department(Department, Course) :-
    course(Course, _, Department).

course_credits(Course, Credits) :-
    credits(Course, Credits).

student_course_count(Student, Count) :-
    student_exists(Student),
    findall(Course, enrolled(Student, Course), Courses),
    sort(Courses, UniqueCourses),
    length(UniqueCourses, Count).

student_total_credits(Student, TotalCredits) :-
    student_exists(Student),
    findall(Course, enrolled(Student, Course), EnrolledCourses),
    sort(EnrolledCourses, Courses),
    findall(Credits,
            ( member(Course, Courses), course_credits(Course, Credits) ),
            CreditValues),
    sum_list(CreditValues, TotalCredits).

course_enrollment_count(Course, Count) :-
    course_exists(Course),
    findall(Student, enrolled(Student, Course), Students),
    sort(Students, UniqueStudents),
    length(UniqueStudents, Count).

common_course(Student1, Student2, Course) :-
    enrolled(Student1, Course),
    enrolled(Student2, Course),
    Student1 \= Student2.

multiple_courses(Student) :-
    student_course_count(Student, Count),
    Count > 1.

can_enroll(Student, Course) :-
    student_exists(Student),
    course_exists(Course),
    \+ enrolled(Student, Course).

available_course(Student, Course) :-
    can_enroll(Student, Course).

print_students :-
    forall(student(Id, Name, Dept),
           format("~w|~w|~w~n", [Id, Name, Dept])).

print_courses :-
    forall(course(Id, Name, Dept),
           ( credits(Id, Cr),
             format("~w|~w|~w|~w~n", [Id, Name, Dept, Cr]) )).

print_student_courses(StudentId) :-
    ( student(StudentId, _, _)
    -> forall(student_courses(StudentId, CourseId),
              ( course(CourseId, CName, _),
                credits(CourseId, Cr),
                format("~w|~w|~w~n", [CourseId, CName, Cr]) ))
    ;  format("ERROR:no_such_student~n")
    ).

print_course_students(CourseId) :-
    ( course(CourseId, _, _)
    -> forall(course_students(CourseId, StudentId),
              ( student(StudentId, SName, SDept),
                format("~w|~w|~w~n", [StudentId, SName, SDept]) ))
    ;  format("ERROR:no_such_course~n")
    ).

print_check_enrollment(StudentId, CourseId) :-
    ( \+ student(StudentId, _, _)
    -> format("ERROR:no_such_student~n")
    ; \+ course(CourseId, _, _)
    -> format("ERROR:no_such_course~n")
    ; is_enrolled(StudentId, CourseId)
    -> format("true~n")
    ;  format("false~n")
    ).

print_common_courses(Student1, Student2) :-
    ( \+ student(Student1, _, _)
    -> format("ERROR:no_such_student~n")
    ; \+ student(Student2, _, _)
    -> format("ERROR:no_such_student~n")
    ;  forall(common_course(Student1, Student2, CourseId),
              ( course(CourseId, CName, _),
                credits(CourseId, Cr),
                format("~w|~w|~w~n", [CourseId, CName, Cr]) ))
    ).

print_course_credits(CourseId) :-
    ( course_credits(CourseId, Cr)
    -> format("~w~n", [Cr])
    ;  format("ERROR:no_such_course~n")
    ).

print_departments :-
    findall(D, student(_, _, D), Ds1),
    findall(D, course(_, _, D), Ds2),
    append(Ds1, Ds2, All),
    sort(All, Unique),
    forall(member(D, Unique), format("~w~n", [D])).

print_department_students(Dept) :-
    forall(students_in_department(Dept, StudentId),
           ( student(StudentId, SName, _),
             format("~w|~w|~w~n", [StudentId, SName, Dept]) )).

print_department_courses(Dept) :-
    forall(courses_in_department(Dept, CourseId),
           ( course(CourseId, CName, _),
             credits(CourseId, Cr),
             format("~w|~w|~w~n", [CourseId, CName, Cr]) )).

print_stats :-
    aggregate_all(count, student(_, _, _), StudentCount),
    aggregate_all(count, course(_, _, _), CourseCount),
    aggregate_all(count, enrolled(_, _), EnrollCount),
    format("~w|~w|~w~n", [StudentCount, CourseCount, EnrollCount]).

print_can_enroll(StudentId, CourseId) :-
    ( \+ student(StudentId, _, _)
    -> format("invalid_student~n")
    ; \+ course(CourseId, _, _)
    -> format("invalid_course~n")
    ; is_enrolled(StudentId, CourseId)
    -> format("already_enrolled~n")
    ;  format("ok~n")
    ).
