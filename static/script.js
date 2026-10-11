let CACHE = {
  students: [],
  courses: [],
  departments: [],
};

function qs(selector) {
  return document.querySelector(selector);
}

function qsa(selector) {
  return Array.from(document.querySelectorAll(selector));
}

async function apiGet(path) {
  const res = await fetch(path);
  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error(data.error || "Something went wrong.");
  }
  return data;
}

async function apiPost(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok || data.success === false) {
    throw new Error(data.message || data.error || "Something went wrong.");
  }
  return data;
}

function showToast(message, type) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.className = "toast " + type;
  toast.hidden = false;
  clearTimeout(showToast._timer);
  showToast._timer = setTimeout(() => { toast.hidden = true; }, 3500);
}

function fillTable(tableId, rows, renderRow) {
  const tbody = qs(`#${tableId} tbody`);
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = renderRow(row);
    tbody.appendChild(tr);
  });
}

function fillSelect(selectEl, items, valueKey, labelFn) {
  selectEl.innerHTML = "";
  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value = item[valueKey];
    opt.textContent = labelFn(item);
    selectEl.appendChild(opt);
  });
}

function switchView(sectionName) {
  qsa(".nav-link").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.section === sectionName);
  });
  qsa(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${sectionName}`);
  });
}

async function loadBaseData() {
  const [students, courses, departments] = await Promise.all([
    apiGet("/api/students"),
    apiGet("/api/courses"),
    apiGet("/api/departments"),
  ]);
  CACHE.students = students;
  CACHE.courses = courses;
  CACHE.departments = departments;

  const studentLabel = (s) => `${s.name} (${s.id})`;
  const courseLabel = (c) => `${c.name} (${c.id})`;

  fillSelect(qs("#enroll-student"), students, "id", studentLabel);
  fillSelect(qs("#enroll-course"), courses, "id", courseLabel);

  fillSelect(qs("#sc-student"), students, "id", studentLabel);

  fillSelect(qs("#cs-course"), courses, "id", courseLabel);

  fillSelect(qs("#ce-student"), students, "id", studentLabel);
  fillSelect(qs("#ce-course"), courses, "id", courseLabel);

  fillSelect(qs("#cc-student1"), students, "id", studentLabel);
  fillSelect(qs("#cc-student2"), students, "id", studentLabel);

  fillSelect(qs("#dept-select"), departments.map((d) => ({ id: d })), "id", (d) => d.id);
}

async function loadDashboard() {
  const stats = await apiGet("/api/stats");
  qs("#stat-students").textContent = stats.students;
  qs("#stat-courses").textContent = stats.courses;
  qs("#stat-enrollments").textContent = stats.enrollments;

  fillTable("table-students", CACHE.students, (s) =>
    `<td>${s.id}</td><td>${s.name}</td><td>${s.department}</td>`);

  fillTable("table-courses", CACHE.courses, (c) =>
    `<td>${c.id}</td><td>${c.name}</td><td>${c.department}</td><td>${c.credits}</td>`);
}

function setupEnroll() {
  qs("#btn-enroll").addEventListener("click", async () => {
    const student_id = qs("#enroll-student").value;
    const course_id = qs("#enroll-course").value;
    try {
      const result = await apiPost("/api/enroll", { student_id, course_id });
      showToast(result.message, "success");
      await loadDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function setupStudentCourses() {
  qs("#btn-student-courses").addEventListener("click", async () => {
    const studentId = qs("#sc-student").value;
    try {
      const courses = await apiGet(`/api/student/${studentId}/courses`);
      fillTable("table-student-courses", courses, (c) =>
        `<td>${c.id}</td><td>${c.name}</td><td>${c.credits}</td>`);
      qs("#note-student-courses").hidden = courses.length > 0;
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function setupCourseStudents() {
  qs("#btn-course-students").addEventListener("click", async () => {
    const courseId = qs("#cs-course").value;
    try {
      const students = await apiGet(`/api/course/${courseId}/students`);
      fillTable("table-course-students", students, (s) =>
        `<td>${s.id}</td><td>${s.name}</td><td>${s.department}</td>`);
      qs("#note-course-students").hidden = students.length > 0;
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function setupCheckEnrollment() {
  qs("#btn-check-enrollment").addEventListener("click", async () => {
    const student = qs("#ce-student").value;
    const course = qs("#ce-course").value;
    try {
      const result = await apiGet(
        `/api/check-enrollment?student=${student}&course=${course}`
      );
      const panel = qs("#check-result-panel");
      const text = qs("#check-result-text");
      panel.hidden = false;
      if (result.enrolled) {
        text.textContent = "Student is enrolled in this course.";
        text.className = "result-line ok";
      } else {
        text.textContent = "Student is not enrolled in this course.";
        text.className = "result-line no";
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function setupCommonCourses() {
  qs("#btn-common-courses").addEventListener("click", async () => {
    const s1 = qs("#cc-student1").value;
    const s2 = qs("#cc-student2").value;
    try {
      const courses = await apiGet(
        `/api/common-courses?student1=${s1}&student2=${s2}`
      );
      fillTable("table-common-courses", courses, (c) =>
        `<td>${c.id}</td><td>${c.name}</td><td>${c.credits}</td>`);
      qs("#note-common-courses").hidden = courses.length > 0;
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function setupDepartments() {
  qs("#btn-departments").addEventListener("click", async () => {
    const dept = qs("#dept-select").value;
    try {
      const [students, courses] = await Promise.all([
        apiGet(`/api/department/${dept}/students`),
        apiGet(`/api/department/${dept}/courses`),
      ]);
      fillTable("table-dept-students", students, (s) =>
        `<td>${s.id}</td><td>${s.name}</td>`);
      fillTable("table-dept-courses", courses, (c) =>
        `<td>${c.id}</td><td>${c.name}</td><td>${c.credits}</td>`);
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  qsa(".nav-link").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.section));
  });

  setupEnroll();
  setupStudentCourses();
  setupCourseStudents();
  setupCheckEnrollment();
  setupCommonCourses();
  setupDepartments();

  try {
    await loadBaseData();
    await loadDashboard();
  } catch (err) {
    showToast(err.message, "error");
  }
});
