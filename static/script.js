// ====================== SIGN UP PART ======================

function showSmsCodeField() {
  const smsCodeSection = document.getElementById("smsCodeSection");
  smsCodeSection.style.display = "block";
  document.getElementById("sms_code").required = true; // Make SMS field required
}

function validateForm() {
  let valid = true;

  // Reset all error messages
  const errors = [
    "nameError",
    "emailError",
    "passwordError",
    "confirmPasswordError",
    "termsError",
    "birthdayError",
    "formMessage",
    "smsCodeError",
  ];
  errors.forEach((id) => (document.getElementById(id).style.display = "none"));

  // Name Validation
  const name = document.getElementById("name").value;
  if (name.length < 3) {
    document.getElementById("nameError").textContent =
      "Name must be at least 3 characters.";
    document.getElementById("nameError").style.display = "inline";
    valid = false;
  }

  // Email Validation
  const email = document.getElementById("email").value;
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
  if (!emailRegex.test(email)) {
    document.getElementById("emailError").textContent =
      "Please enter a valid email.";
    document.getElementById("emailError").style.display = "inline";
    valid = false;
  }

  // Password Validation
  const password = document.getElementById("password").value;
  if (password.length < 8) {
    document.getElementById("passwordError").textContent =
      "Password must be at least 8 characters.";
    document.getElementById("passwordError").style.display = "inline";
    valid = false;
  }

  // Confirm Password Validation
  const confirmPassword = document.getElementById("confirm-password").value;
  if (password !== confirmPassword) {
    document.getElementById("confirmPasswordError").textContent =
      "Passwords do not match.";
    document.getElementById("confirmPasswordError").style.display = "inline";
    valid = false;
  }

  // If the SMS code field is visible, validate it
  const smsCodeField = document.getElementById("sms_code");
  if (smsCodeField && smsCodeField.style.display === "block") {
    const smsCode = smsCodeField.value.trim();
    if (smsCode === "") {
      document.getElementById("smsCodeError").textContent =
        "Please enter the SMS code.";
      document.getElementById("smsCodeError").style.display = "inline";
      valid = false;
    }
  }

  // Birthday Validation (6+ years old)
  const birthday = new Date(document.getElementById("birthday").value);
  const today = new Date();
  const age = today.getFullYear() - birthday.getFullYear();
  const month = today.getMonth() - birthday.getMonth();
  if (month < 0 || (month === 0 && today.getDate() < birthday.getDate())) {
    age--;
  }

  if (age < 6) {
    document.getElementById("birthdayError").textContent =
      "You must be at least 6 years old.";
    document.getElementById("birthdayError").style.display = "inline";
    valid = false;
  }

  // Terms and Conditions Checkbox
  const terms = document.getElementById("terms").checked;
  if (!terms) {
    document.getElementById("termsError").textContent =
      "You must agree to the terms and conditions.";
    document.getElementById("termsError").style.display = "inline";
    valid = false;
  }

  // Display success or error message
  if (valid) {
    document.getElementById("formMessage").textContent =
      "Registration successful!";
    document.getElementById("formMessage").style.display = "inline";
    console.log("success");
    saveUser(); // Save user details to localStorage
  } else {
    console.log("not success");
  }

  return valid;
}

// ====================== LOG IN PART ======================

function validateLoginForm(event) {
  let valid = true;

  // Reset error messages
  const errors = ["emailLoginError", "passwordLoginError", "loginMessage"];
  errors.forEach((id) => (document.getElementById(id).style.display = "none"));

  // Email Validation
  const email = document.getElementById("email").value;
  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
  if (!emailRegex.test(email)) {
    document.getElementById("emailLoginError").textContent =
      "Please enter a valid email.";
    document.getElementById("emailLoginError").style.display = "inline";
    valid = false;
  }

  // Password Validation
  const password = document.getElementById("password").value;
  if (password.length < 8) {
    document.getElementById("passwordLoginError").textContent =
      "Password must be at least 8 characters.";
    document.getElementById("passwordLoginError").style.display = "inline";
    valid = false;
  }

  // If the form is valid, let it submit to the server
  if (valid) {
    return true;
  } else {
    event.preventDefault();
    return false;
  }
}

// ====================== GLOBAL VARIABLES ======================
let state = {
  courseId: null, 
  teacherId: document.getElementById('teacherData')?.dataset.teacherId || null, // Get from hidden element
  groupId: null, 
  groupName: null,
  currentDay: null, 
  hasUnsavedChanges: false,
  deleteUserId: null,
};

const els = {
  courseSelect: document.getElementById("courseSelect"),
  teacherSelect: document.getElementById("teacherSelect"),
  groupSelect: document.getElementById("groupSelect"),
  journalTable: document.getElementById("journalTable"),
  addDayBtn: document.getElementById("addDayButton"),
  submitBtn: document.getElementById("submitAttendanceButton"),
  deleteUserIdInput: document.getElementById("deleteUserId"),
  confirmDeleteUserBtn: document.getElementById("confirmDeleteUserButton"),
};

// ====================== MODAL FUNCTIONS ======================
async function showAddDayModal() {
  if (!state.courseId || !state.groupName) {
    return alert("Select course and group first");
  }

  try {
    const res = await fetch(`/get_max_day/${state.courseId}/${state.groupName}`);
    const data = await res.json();
    if (!data.success) throw Error(data.error || "Failed to get max day");

    const newDayInput = document.getElementById("newDayInput");
    const newDayDateInput = document.getElementById("newDayDateInput");
    const addDayModal = document.getElementById("addDayModal");

    newDayInput.value = (data.max_day || 0) + 1;
    newDayDateInput.valueAsDate = new Date();
    addDayModal.style.display = "block";
  } catch (e) {
    console.error("Error preparing new day:", e);
    alert("Failed to prepare new day: " + e.message);
  }
}



async function confirmAddDay() {
  const dayInput = document.getElementById("newDayInput");
  const dayDateInput = document.getElementById("newDayDateInput");
  if (!dayInput || !dayDateInput || !dayInput.value || !dayDateInput.value) {
    return alert("Fill all fields");
  }

  try {
    const btn = document.getElementById("confirmAddDayButton");
    btn.disabled = true;
    btn.textContent = "Activating...";

    const res = await fetch("/add_day", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: state.courseId,
        group_name: state.groupName,
        teacher_id: state.teacherId,
        day: parseInt(dayInput.value),
        day_date: dayDateInput.value
      })
    });

    const data = await res.json();
    if (!res.ok) throw Error(data.error || "Failed to activate day");

    document.getElementById("addDayModal").style.display = "none";
    state.currentDay = parseInt(dayInput.value);
    state.hasUnsavedChanges = true;
    toggleAttendanceButtons(true);
    await loadJournalTable();
  } catch (e) {
    console.error("Error adding day:", e);
    alert("Failed to activate day: " + e.message);
    toggleAttendanceButtons(false);
  } finally {
    const btn = document.getElementById("confirmAddDayButton");
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Activate";
    }
  }
}

function toggleAttendanceButtons(isActivated) {
  const activateBtn = document.getElementById("addDayButton");
  const submitBtn = document.getElementById("submitAttendanceButton");
  
  if (activateBtn && submitBtn) {
    activateBtn.style.display = isActivated ? "none" : "inline-block";
    submitBtn.style.display = isActivated ? "inline-block" : "none";
  }
}

async function submitAttendance() {
  if (!state.courseId || !state.groupName || !state.currentDay) {
    return alert("Activate a day first");
  }

  try {
    const submitBtn = document.getElementById("submitAttendanceButton");
    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting...";

    const attendanceData = [];
    document.querySelectorAll("#journalTable tbody tr").forEach(row => {
      const userId = row.cells[0].textContent;
      const dayCell = row.querySelector(`td[data-day="${state.currentDay}"]`);
      if (dayCell) {
        const select = dayCell.querySelector("select.attendance-select");
        attendanceData.push({
          user_id: userId,
          status: select?.value || "0"
        });
      }
    });

    const res = await fetch("/submit_attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: state.courseId,
        group_name: state.groupName,
        day: state.currentDay,
        attendance: attendanceData
      })
    });

    const data = await res.json();
    if (!res.ok) throw Error(data.error || "Failed to submit");

    alert("Attendance submitted!");
    state.hasUnsavedChanges = false;
    state.currentDay = null;
    toggleAttendanceButtons(false);
    await loadJournalTable();
  } catch (e) {
    console.error("Error submitting:", e);
    alert("Failed to submit: " + e.message);
  } finally {
    const submitBtn = document.getElementById("submitAttendanceButton");
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit";
    }
  }
}


async function showCreateGroupModal() {
  try {
    const res = await fetch('/get_all_teachers');
    const teachers = await res.json();
    const select = document.getElementById('teacherSelectForGroup');
    select.innerHTML = '<option value="">Select Teacher</option>';
    teachers.forEach(teacher => {
      select.add(new Option(teacher.name, teacher.id));
    });
  } catch (e) {
    console.error('Error loading teachers:', e);
  }
  document.getElementById("createGroupModal").style.display = "block";
}

async function createGroup() {
  const courseId = document.getElementById("courseSelectForGroup").value;
  const teacherId = document.getElementById("teacherSelectForGroup").value;
  const groupName = document.getElementById("groupNameInput").value.trim();
  const userIds = document.getElementById("userIdsInput").value.trim()
    .split(",").map(id => parseInt(id.trim())).filter(id => !isNaN(id));

  if (!courseId || !teacherId || !groupName) return alert("Fill required fields");
  if (userIds.length === 0) return alert("Enter valid user IDs");

  try {
    const btn = document.getElementById("confirmCreateGroupButton");
    btn.disabled = true;
    btn.textContent = "Creating...";

    const res = await fetch("/create_group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: parseInt(courseId), 
        teacher_id: parseInt(teacherId),
        group_name: groupName, 
        user_ids: userIds
      })
    });

    const data = await res.json();
    if (!res.ok) {
      if (data.students) {
        // Handle case where students are already in a group
        const studentList = data.students.map(s => `ID: ${s.id}, Name: ${s.name}`).join('\n');
        alert(`Cannot create group. These students are already in a group for this course:\n${studentList}`);
        return;
      }
      if (data.existing) {
        alert(`Group name "${groupName}" already exists in the system. Please choose a different name.`);
        return;
      }
      throw Error(data.error || "Failed to create group");
    }

    alert(`Group "${data.group.name}" created successfully!`);
    document.getElementById("createGroupModal").style.display = "none";
    document.getElementById("groupNameInput").value = "";
    document.getElementById("userIdsInput").value = "";

    // Force page reload after successful group creation
    window.location.reload();

  } catch (e) {
    console.error("Error creating group:", e);
    alert(`Error: ${e.message}`);
  } finally {
    const btn = document.getElementById("confirmCreateGroupButton");
    if (btn) { btn.disabled = false; btn.textContent = "Create Group"; }
  }
}

// ====================== CORE FUNCTIONS ======================
async function handleSelectionChange(type, value) {
  if (state.hasUnsavedChanges && !confirm("You have unsaved changes. Continue?")) {
    if (type === "course") els.courseSelect.value = state.courseId;
    else if (type === "teacher" && els.teacherSelect) els.teacherSelect.value = state.teacherId;
    else els.groupSelect.value = state.groupName;
    return;
  }

  if (type === "course") {
    state.courseId = value;
    if (document.getElementById('teacherSelect')) {
      await loadTeachers();
    } else {
      // For teacher dashboard
      await loadGroups();
    }
  } else if (type === "teacher") {
    state.teacherId = value;
    await loadGroups();
  } else if (type === "group") {
    state.groupName = value;
    await loadJournalTable();
  }
  resetFormState();
}

async function loadTeachers() {
  if (!state.courseId) return;

  try {
    els.teacherSelect.innerHTML = "<option value=''>Select Teacher</option>";
    els.teacherSelect.disabled = false;

    const res = await fetch(`/get_course_teachers_with_groups/${state.courseId}`);
    const teachers = await res.json();

    teachers.forEach(teacher => {
      els.teacherSelect.add(new Option(teacher.name, teacher.id));
    });
    resetGroupDropdown();
  } catch (e) {
    console.error("Error loading teachers:", e);
    alert("Failed to load teachers");
  }
}

async function loadGroups() {
  if (!state.courseId || !state.teacherId) return;

  try {
    resetGroupDropdown();
    els.groupSelect.disabled = false;

    const response = await fetch(`/get_teacher_groups/${state.courseId}/${state.teacherId}`);
    const data = await response.json();
    
    if (data.success) {
      els.groupSelect.innerHTML = '<option value="">Select Group</option>';
      data.groups.forEach(group => {
        els.groupSelect.add(new Option(group, group));
      });
    }
  } catch (e) {
    console.error("Error loading groups:", e);
    alert(`Failed to load groups: ${e.message}`);
  }
}


async function loadJournalTable() {
  if (!state.courseId || !state.groupName) return;

  try {
    const res = await fetch(`/get_journal_data/${state.courseId}/${state.groupName}`);
    const data = await res.json();
    if (!data.success) throw Error(data.error || "Failed to load data");

    state.groupId = data.group.id;
    state.teacherId = data.group.teacher_id;
    state.maxDay = data.max_day;

    const thead = els.journalTable.querySelector("thead");
    const tbody = els.journalTable.querySelector("tbody");
    thead.innerHTML = "<tr><th>ID</th><th>Name</th>";
    tbody.innerHTML = "";

    // Add day headers
    Object.keys(data.attendance).sort((a, b) => a - b).forEach(day => {
      const date = data.attendance[day][0].day_date || "";
      thead.querySelector("tr").innerHTML += `<th>Day ${day}<br>${date}</th>`;
    });

    // Add student rows
    data.students.forEach(student => {
      const row = document.createElement("tr");
      row.innerHTML = `<td>${student.id}</td><td>${student.name}</td>`;

      Object.keys(data.attendance).sort((a, b) => a - b).forEach(day => {
        const cell = document.createElement("td");
        cell.setAttribute("data-day", day);

        const record = data.attendance[day].find(r => r.user_id === student.id);
        if (record?.status) {
          cell.textContent = record.status;
        } else {
          const select = document.createElement("select");
          select.className = "attendance-select";
          select.innerHTML = `
            <option value="i/e" selected>i/e</option>
            <option value="q/b">q/b</option>
            ${Array.from({ length: 11 }, (_, i) => `<option value="${i}">${i}</option>`).join('')}`;
          cell.appendChild(select);
          select.addEventListener("change", () => state.hasUnsavedChanges = true);
        }
        row.appendChild(cell);
      });
      tbody.appendChild(row);
    });
  } catch (e) {
    console.error("Error loading journal:", e);
    alert("Failed to load journal data");
  }
}

async function submitAttendance() {
  if (!state.courseId || !state.groupName || !state.currentDay) {
    return alert("Activate a day first");
  }

  try {
    els.submitBtn.disabled = true;
    els.submitBtn.textContent = "Submitting...";

    const attendanceData = [];
    els.journalTable.querySelectorAll("tbody tr").forEach(row => {
      const userId = row.cells[0].textContent;
      const dayCell = row.querySelector(`td[data-day="${state.currentDay}"]`);
      if (dayCell) {
        const select = dayCell.querySelector("select.attendance-select");
        attendanceData.push({
          user_id: userId,
          status: select?.value || "0"
        });
      }
    });

    const res = await fetch("/submit_attendance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        course_id: state.courseId, group_name: state.groupName,
        day: state.currentDay, attendance: attendanceData
      })
    });

    const data = await res.json();
    if (!res.ok) throw Error(data.error || "Failed to submit");

    alert("Attendance submitted!");
    state.hasUnsavedChanges = false;
    state.currentDay = null;
    els.addDayBtn.style.display = "inline-block";
    els.submitBtn.style.display = "none";
    await loadJournalTable();
  } catch (e) {
    console.error("Error submitting:", e);
    alert("Failed to submit: " + e.message);
  } finally {
    if (els.submitBtn) {
      els.submitBtn.disabled = false;
      els.submitBtn.textContent = "Submit";
    }
  }
}

function resetFormState() {
  if (els.addDayBtn) els.addDayBtn.style.display = "inline-block";
  if (els.submitBtn) els.submitBtn.style.display = "none";
  state.hasUnsavedChanges = false;
}

function resetGroupDropdown() {
  els.groupSelect.innerHTML = "<option value=''>Select Group</option>";
  els.groupSelect.disabled = true;
}

// ====================== INITIALIZATION ======================
function setupEventListeners() {
  els.courseSelect?.addEventListener("change", () => handleSelectionChange("course", els.courseSelect.value));
  els.teacherSelect?.addEventListener("change", () => handleSelectionChange("teacher", els.teacherSelect.value));
  els.groupSelect?.addEventListener("change", () => handleSelectionChange("group", els.groupSelect.value));
  els.addDayBtn?.addEventListener("click", showAddDayModal);
  els.submitBtn?.addEventListener("click", submitAttendance);

  document.getElementById("createGroupButton")?.addEventListener("click", showCreateGroupModal);
  document.getElementById("confirmAddDayButton")?.addEventListener("click", confirmAddDay);
  document.getElementById("confirmCreateGroupButton")?.addEventListener("click", createGroup);
  document.getElementById("deleteUserButton")?.addEventListener("click", () => {
    if (!state.courseId || !state.teacherId || !state.groupId) {
      return alert("Please select course, teacher and group first");
    }
    document.getElementById("deleteUserModal").style.display = "block";
  });
  els.confirmDeleteUserBtn?.addEventListener("click", deleteUserFromGroup);
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const userId = this.getAttribute('data-user-id');
        deleteUser(userId);
    });
  });

  setupModalCloseHandlers();
}

function setupModalCloseHandlers() {
  // Close modals when clicking the X button
  document.querySelectorAll('.modal .close').forEach(closeBtn => {
    closeBtn.addEventListener('click', function () {
      this.closest('.modal').style.display = 'none';
    });
  });

  // Close modals when clicking outside content
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function (e) {
      if (e.target === this) {
        this.style.display = 'none';
      }
    });
  });
}

async function deleteUserFromGroup() {
  if (!state.groupId || !els.deleteUserIdInput.value) {
    return alert("Select group and enter user ID");
  }

  try {
    els.confirmDeleteUserBtn.disabled = true;
    
    const response = await fetch(`/delete_user_from_group/${state.groupId}/${els.deleteUserIdInput.value}`, {
      method: "DELETE"
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || "Failed to delete user");
    }
    
    document.getElementById("deleteUserModal").style.display = "none";
    els.deleteUserIdInput.value = "";
    
    if (data.group_deleted) {
      window.location.reload(); // Simply reload the entire page
    } else {
      await loadJournalTable();
    }
    
    alert(data.message || "Operation completed successfully");
  } catch (error) {
    console.error("Delete error:", error);
    alert(`Error: ${error.message}`);
  } finally {
    els.confirmDeleteUserBtn.disabled = false;
  }
}

async function checkTeacherHasGroups(courseId, teacherId) {
  try {
    const response = await fetch(`/check_teacher_groups/${courseId}/${teacherId}`);
    const data = await response.json();
    return data.has_groups;
  } catch (error) {
    console.error("Error checking teacher groups:", error);
    return false;
  }
}

async function deleteUser(userId) {
  if (!confirm("Are you sure you want to delete this user?")) return;
  
  try {
      const response = await fetch(`/delete_user/${userId}`, {
          method: 'POST',
          headers: { 
              'Content-Type': 'application/json',
          }
      });
      
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Failed to delete user');
      
      // Always reload the page after successful deletion
      window.location.reload();
      
  } catch (error) {
      console.error('Delete error:', error);
      alert(`Error: ${error.message}`);
  }
}

function getCSRFToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

document.getElementById("addTeacherButton")?.addEventListener("click", () => {
  document.getElementById("addTeacherModal").style.display = "block";
});

async function registerTeacher(event) {
  event.preventDefault();
  
  const teacherData = {
    name: document.getElementById("teacherName").value.trim(),
    email: document.getElementById("teacherEmail").value.trim(),
    phone: document.getElementById("teacherPhone").value.trim(),
    birthday: document.getElementById("teacherBirthday").value,
    password: document.getElementById("teacherPassword").value,
    role: "teacher"
  };

  // Simple validation
  if (!teacherData.name || !teacherData.email || !teacherData.phone || 
      !teacherData.birthday || !teacherData.password) {
    return alert("Please fill all fields");
  }

  try {
    const btn = document.getElementById("confirmAddTeacher");
    btn.disabled = true;
    btn.textContent = "Registering...";

    const response = await fetch("/register_teacher", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(teacherData)
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Registration failed");

    alert("Teacher registered successfully!");
    document.getElementById("addTeacherModal").style.display = "none";
    document.getElementById("teacherForm").reset();
    window.location.reload(); // Refresh to show new teacher
  } catch (error) {
    console.error("Error registering teacher:", error);
    alert("Error: " + error.message);
  } finally {
    const btn = document.getElementById("confirmAddTeacher");
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Register Teacher";
    }
  }
}

document.getElementById("teacherForm")?.addEventListener("submit", registerTeacher); 

function setupTableFilters() {
  // Admin Panel Filters
  const adminTable = document.querySelector('.dashboard-panel:last-child table');
  if (adminTable) {
      const roleFilter = document.getElementById('roleFilter');
      const searchInput = document.getElementById('searchInput');
      const adminRows = adminTable.querySelectorAll('tbody tr');

      function filterAdminTable() {
          const roleValue = roleFilter.value.toLowerCase();
          const searchValue = searchInput.value.trim();
          
          adminRows.forEach(row => {
              const cells = row.querySelectorAll('td');
              if (cells.length < 7) return;
              
              const role = cells[3].textContent.toLowerCase();
              const name = cells[1].textContent;
              const email = cells[2].textContent;
              const phone = cells[4].textContent;
              const id = cells[0].textContent;
              
              // Role filter remains the same
              const roleMatch = !roleValue || role === roleValue;
              
              // New exact partial matching for search
              let searchMatch = false;
              if (!searchValue) {
                  searchMatch = true;
              } else {
                  // Check if search value matches the beginning of any field
                  searchMatch = 
                      id.startsWith(searchValue) ||
                      phone.startsWith(searchValue) ||
                      email.startsWith(searchValue) ||
                      name.toLowerCase().startsWith(searchValue.toLowerCase());
              }
              
              row.style.display = roleMatch && searchMatch ? '' : 'none';
          });
      }

      if (roleFilter) roleFilter.addEventListener('change', filterAdminTable);
      if (searchInput) searchInput.addEventListener('input', filterAdminTable);
  }

  // Students Waiting Filters
  const waitingTable = document.getElementById('waitingStudentsTable');
  if (waitingTable) {
      const courseFilter = document.getElementById('waitingCourseFilter');
      const waitingRows = waitingTable.querySelectorAll('tbody tr');

      function filterWaitingTable() {
          const courseValue = courseFilter.value.toLowerCase();
          
          waitingRows.forEach(row => {
              const cells = row.querySelectorAll('td');
              if (cells.length < 6) return;
              
              const course = cells[3].textContent.toLowerCase();
              row.style.display = !courseValue || course.includes(courseValue) ? '' : 'none';
          });
      }

      if (courseFilter) courseFilter.addEventListener('change', filterWaitingTable);
  }
}



// File Upload Functions
async function setupFileUpload(courseId) {
  const form = document.getElementById('fileUploadForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('courseFile');
      const submitBtn = form.querySelector('button[type="submit"]');
      
      if (!fileInput.files.length) {
          alert('Please select a file to upload');
          return;
      }

      const file = fileInput.files[0];
      
      // Client-side validation
      const allowedTypes = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'zip'];
      const fileExt = file.name.split('.').pop().toLowerCase();
      
      if (!allowedTypes.includes(fileExt)) {
          alert('File type not allowed. Allowed types: ' + allowedTypes.join(', '));
          return;
      }

      if (file.size > 5 * 1024 * 1024) {
          alert('File size exceeds 5MB limit');
          return;
      }

      const formData = new FormData();
      formData.append('file', file);

      try {
          // Show loading state
          submitBtn.disabled = true;
          submitBtn.textContent = 'Uploading...';

          const response = await fetch(`/upload_file/${courseId}`, {
              method: 'POST',
              body: formData
          });
          
          const data = await response.json();

          if (!response.ok) {
              throw new Error(data.error || 'Upload failed');
          }

          if (data.success) {
              alert('File uploaded successfully!');
              loadFiles(courseId);
              fileInput.value = '';
          } else {
              throw new Error(data.error || 'Upload failed');
          }
      } catch (error) {
          console.error('Upload error:', error);
          alert('Error: ' + error.message);
      } finally {
          // Reset button state
          submitBtn.disabled = false;
          submitBtn.textContent = 'Upload';
      }
  });
}

async function loadFiles(courseId) {
  const fileList = document.getElementById('fileList');
  if (!fileList) return;

  try {
      const response = await fetch(`/get_files/${courseId}`);
      const data = await response.json();

      if (data.success) {
          if (data.files.length === 0) {
              fileList.innerHTML = '<p>No files uploaded yet.</p>';
              return;
          }

          fileList.innerHTML = '<div class="file-list"></div>';
          const listContainer = fileList.querySelector('.file-list');

          data.files.forEach(file => {
              const fileCard = document.createElement('div');
              fileCard.className = 'file-card';
              fileCard.innerHTML = `
                  <div class="file-card-header">
                      <span class="file-name" title="${file.name}">${file.name}</span>
                      <span class="file-type">${file.type.toUpperCase()}</span>
                  </div>
                  <div class="file-meta">
                      <div>Size: ${formatFileSize(file.size)}</div>
                      <div>Uploaded: ${file.uploaded_at}</div>
                      ${file.user_name ? `<div>By: ${file.user_name}</div>` : ''}
                  </div>
                  <div class="file-actions">
                      <button class="download-btn" data-file="${file.path}" data-name="${file.name}">
                          Download
                      </button>
                      <button class="delete-btn" data-id="${file.id}">
                          Delete
                      </button>
                  </div>
              `;
              listContainer.appendChild(fileCard);
          });

          // Add event listeners
          document.querySelectorAll('.download-btn').forEach(btn => {
              btn.addEventListener('click', () => {
                  const filePath = btn.getAttribute('data-file');
                  const fileName = btn.getAttribute('data-name');
                  downloadFile(filePath, fileName);
              });
          });

          document.querySelectorAll('.delete-btn').forEach(btn => {
              btn.addEventListener('click', async () => {
                  if (confirm('Are you sure you want to delete this file?')) {
                      const fileId = btn.getAttribute('data-id');
                      await deleteFile(fileId, courseId);
                  }
              });
          });
      }
  } catch (error) {
      console.error('Error loading files:', error);
      fileList.innerHTML = '<p>Error loading files. Please try again.</p>';
  }
}

async function deleteFile(fileId, courseId) {
  try {
      const response = await fetch(`/delete_file/${fileId}`, {
          method: 'DELETE'
      });
      const data = await response.json();

      if (data.success) {
          loadFiles(courseId);
      } else {
          alert(data.error || 'Failed to delete file');
      }
  } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete file');
  }
}

function downloadFile(filePath, fileName) {
  const link = document.createElement('a');
  link.href = `/static/uploads/${filePath}`;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize on course page
if (window.location.pathname.startsWith('/course/')) {
  const courseId = window.location.pathname.split('/')[2];
  setupFileUpload(courseId);
  loadStudentFiles(courseId);
  setupStudentUpload(courseId); // Add this line
}

// Teacher File Management
if (document.getElementById('teacherFileList')) {
  const courseFilterFiles = document.getElementById('filesCourseSelect'); // Corrected ID
  if (courseFilterFiles) {
    courseFilterFiles.addEventListener('change', function() {
      const courseId = this.value;
      if (courseId) {
        loadFiles(courseId, true);
      } else {
        const teacherFileList = document.getElementById('teacherFileList');
        if (teacherFileList) {
          teacherFileList.innerHTML = '<p>Select a course to view files</p>';
        }
      }
    });
  } else {
    console.log('filesCourseSelect element not found - skipping setup');
  }
}

async function loadFiles(courseId, isTeacher = false) {
  const containerId = isTeacher ? 'teacherFileList' : 'fileList';
  const fileList = document.getElementById(containerId);
  if (!fileList) return;

  try {
      const response = await fetch(`/get_files/${courseId}`);
      const data = await response.json();

      if (data.success) {
          if (data.files.length === 0) {
              fileList.innerHTML = '<p>No files uploaded yet.</p>';
              return;
          }

          fileList.innerHTML = '<div class="file-list"></div>';
          const listContainer = fileList.querySelector('.file-list');

          data.files.forEach(file => {
              const fileCard = document.createElement('div');
              fileCard.className = 'file-card';
              fileCard.innerHTML = `
                  <div class="file-card-header">
                      <span class="file-name" title="${file.name}">${file.name}</span>
                      <span class="file-type">${file.type.toUpperCase()}</span>
                  </div>
                  <div class="file-meta">
                      <div>Size: ${formatFileSize(file.size)}</div>
                      <div>Uploaded: ${file.uploaded_at}</div>
                      ${file.user_name ? `<div>By: ${file.user_name}</div>` : ''}
                  </div>
                  <div class="file-actions">
                      <button class="download-btn" data-file="${file.path}" data-name="${file.name}">
                          Download
                      </button>
                      ${isTeacher ? `<button class="delete-btn" data-id="${file.id}">
                          Delete
                      </button>` : ''}
                  </div>
              `;
              listContainer.appendChild(fileCard);
          });

          // Add event listeners
          document.querySelectorAll('.download-btn').forEach(btn => {
              btn.addEventListener('click', () => {
                  const filePath = btn.getAttribute('data-file');
                  const fileName = btn.getAttribute('data-name');
                  downloadFile(filePath, fileName);
              });
          });

          if (isTeacher) {
              document.querySelectorAll('.delete-btn').forEach(btn => {
                  btn.addEventListener('click', async () => {
                      if (confirm('Are you sure you want to delete this file?')) {
                          const fileId = btn.getAttribute('data-id');
                          await deleteFile(fileId, courseId);
                          loadFiles(courseId, isTeacher);
                      }
                  });
              });
          }
      }
  } catch (error) {
      console.error('Error loading files:', error);
      fileList.innerHTML = '<p>Error loading files. Please try again.</p>';
  }
} 


// ====================== TEACHER FILE MANAGEMENT ======================

let fileState = {
  courseId: null,
  groupId: null,
  day: null
};

async function loadFilesForGroupDay(courseId, groupId, day) {
  try {
    const response = await fetch(`/get_group_files/${groupId}/${day}`);
    const data = await response.json();
    
    if (data.success) {
      renderTeacherFiles(data.files);
    } else {
      const container = document.getElementById('teacherFileList');
      container.innerHTML = '<p>No files found for this day</p>';
    }
  } catch (error) {
    console.error('Error loading files:', error);
    const container = document.getElementById('teacherFileList');
    container.innerHTML = '<p>Error loading files</p>';
  }
}

function renderTeacherFiles(files) {
  const container = document.getElementById('teacherFileList');
  container.innerHTML = '';
  
  if (!files || files.length === 0) {
    container.innerHTML = '<p>No files uploaded for this day</p>';
    return;
  }

  // Group by student
  const filesByUser = files.reduce((acc, file) => {
    const key = file.user_id;
    if (!acc[key]) acc[key] = [];
    acc[key].push(file);
    return acc;
  }, {});

  Object.entries(filesByUser).forEach(([userId, userFiles]) => {
    const userSection = document.createElement('div');
    userSection.className = 'student-file-section';
    
    userSection.innerHTML = `
      <h3>${userFiles[0].user_name}</h3>
      <div class="student-files-list">
        ${userFiles.map(file => `
          <div class="file-card">
            <div class="file-info">
              <span class="file-name">${file.file_name}</span>
              <span class="file-type">${file.file_type.toUpperCase()}</span>
              <span class="file-size">${formatFileSize(file.file_size)}</span>
            </div>
            <div class="file-actions">
              <button class="download-btn" 
                data-file="${file.file_path}" 
                data-name="${file.file_name}">
                Download
              </button>
              ${file.is_teacher_upload ? `
              <button class="delete-btn" data-id="${file.id}">
                Delete
              </button>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
    
    container.appendChild(userSection);
  });
}



function renderStudentFiles(files) {
  const container = document.getElementById('teacherFileList');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (!files || files.length === 0) {
    container.innerHTML = '<p>No files uploaded for this day</p>';
    return;
  }
  
  // Group files by student
  const filesByStudent = {};
  files.forEach(file => {
    if (!filesByStudent[file.user_id]) {
      filesByStudent[file.user_id] = {
        name: file.user_name,
        files: []
      };
    }
    filesByStudent[file.user_id].files.push(file);
  });
  
  // Create UI for each student
  Object.keys(filesByStudent).forEach(studentId => {
    const student = filesByStudent[studentId];
    const studentSection = document.createElement('div');
    studentSection.className = 'student-file-section';
    
    const studentHeader = document.createElement('h3');
    studentHeader.textContent = student.name;
    studentSection.appendChild(studentHeader);
    
    const filesList = document.createElement('div');
    filesList.className = 'student-files-list';
    
    student.files.forEach(file => {
      const fileCard = document.createElement('div');
      fileCard.className = 'file-card';
      fileCard.innerHTML = `
        <div class="file-info">
          <span class="file-name">${file.file_name}</span>
          <span class="file-type">${file.file_type.toUpperCase()}</span>
          <span class="file-size">${formatFileSize(file.file_size)}</span>
        </div>
        <div class="file-actions">
          <button class="download-btn" data-file="${file.file_path}" data-name="${file.file_name}">
            Download
          </button>
          <button class="delete-btn" data-id="${file.id}">
            Delete
          </button>
        </div>
      `;
      filesList.appendChild(fileCard);
    });
    
    studentSection.appendChild(filesList);
    container.appendChild(studentSection);
  });
  
  // Add event listeners
  document.querySelectorAll('.download-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const filePath = btn.getAttribute('data-file');
      const fileName = btn.getAttribute('data-name');
      downloadFile(filePath, fileName);
    });
  });
  
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to delete this file?')) {
        const fileId = btn.getAttribute('data-id');
        await deleteFile(fileId);
        loadFilesForGroupDay(fileState.courseId, fileState.groupId, fileState.day);
      }
    });
  });
}

async function setupTeacherFileManagement() {
  const filesCourseSelect = document.getElementById('filesCourseSelect');
  const filesGroupSelect = document.getElementById('filesGroupSelect');
  const filesDaySelect = document.getElementById('filesDaySelect');

  filesCourseSelect.addEventListener('change', async () => {
    filesGroupSelect.disabled = true;
    filesGroupSelect.innerHTML = '<option value="">Loading...</option>';
    filesDaySelect.disabled = true;
    
    if (filesCourseSelect.value) {
      await loadGroupsForFiles(filesCourseSelect.value);
    }
  });

  filesGroupSelect.addEventListener('change', async () => {
    filesDaySelect.disabled = true;
    if (filesGroupSelect.value) {
      await loadDaysForGroup(filesGroupSelect.value);
    }
  });

  document.getElementById('teacherFileUploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('teacherFileInput').files[0]);
    formData.append('course_id', filesCourseSelect.value);
    formData.append('group_name', filesGroupSelect.value);
    formData.append('day', filesDaySelect.value);

    try {
      const response = await fetch('/upload_group_file', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.success) {
        alert('File uploaded successfully!');
        loadFilesForGroupDay(filesCourseSelect.value, filesGroupSelect.value, filesDaySelect.value);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Error uploading file');
    }
  });
}




async function loadGroupsForFiles(courseId) {
  const response = await fetch(`/get_teacher_groups/${courseId}/${state.teacherId}`);
  const data = await response.json();
  
  if (data.success) {
    const filesGroupSelect = document.getElementById('filesGroupSelect');
    filesGroupSelect.innerHTML = '<option value="">Select Group</option>';
    data.groups.forEach(group => {
      filesGroupSelect.add(new Option(group, group));
    });
    filesGroupSelect.disabled = false;
  }
}

async function loadDaysForGroup(groupName) {
  const response = await fetch(`/get_group_days_by_name/${groupName}`);
  const data = await response.json();
  
  if (data.success) {
    const filesDaySelect = document.getElementById('filesDaySelect');
    filesDaySelect.innerHTML = '<option value="">Select Day</option>';
    data.days.forEach(day => {
      filesDaySelect.add(new Option(`Day ${day.day} - ${day.date}`, day.day));
    });
    filesDaySelect.disabled = false;
  }
}




// ====================== STUDENT FILE DOWNLOAD ======================








function showFileError(message) {
  const errorContainer = document.getElementById('fileError');
  if (errorContainer) {
    errorContainer.textContent = message;
    errorContainer.style.display = 'block';
  }
}


function renderStudentFileList(files) {
  const container = document.getElementById('studentFileList');
  container.innerHTML = '';
  
  const grouped = files.reduce((acc, file) => {
    const key = `Day ${file.day}`;
    if (!acc[key]) acc[key] = [];
    acc[key].push(file);
    return acc;
  }, {});

  Object.entries(grouped).forEach(([day, dayFiles]) => {
    const section = document.createElement('div');
    section.className = 'file-day-section';
    
    section.innerHTML = `
      <h3>${day}</h3>
      <div class="file-list">
        ${dayFiles.map(file => `
          <div class="file-card">
            <div class="file-info">
              <span class="file-name">${file.file_name}</span>
              <span class="file-type">${file.file_type.toUpperCase()}</span>
              <span class="file-size">${formatFileSize(file.file_size)}</span>
              <span class="file-uploader">Uploaded by: ${file.uploader}</span>
            </div>
            <div class="file-actions">
              <button class="download-btn" 
                data-file="${file.file_path}" 
                data-name="${file.file_name}">
                Download
              </button>
              ${!file.is_teacher ? `
              <button class="delete-btn" data-id="${file.id}">
                Delete
              </button>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
    
    container.appendChild(section);
  });
}


function populateDayFilter(files) {
  const dayFilter = document.getElementById('studentDayFilter');
  if (!dayFilter) return;
  
  // Get unique days
  const days = [...new Set(files.map(file => file.day))].sort((a, b) => a - b);
  
  // Clear and repopulate
  dayFilter.innerHTML = '<option value="">All Days</option>';
  days.forEach(day => {
    dayFilter.add(new Option(`Day ${day}`, day));
  });
  
  // Add filter event
  dayFilter.addEventListener('change', () => {
    const selectedDay = dayFilter.value;
    if (selectedDay) {
      const filteredFiles = files.filter(file => file.day == selectedDay);
      renderStudentFileList(filteredFiles);
    } else {
      renderStudentFileList(files);
    }
  });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function() {
  setupEventListeners();
  setupTableFilters();
  
  if (document.getElementById('teacherFilesContainer')) {
    setupTeacherFileUpload();
  }
  if (document.getElementById('studentFilesContainer')) {
    setupStudentFileUpload();
  }
});



function setupFileManagement() {
  // Student file management (course page)
  if (window.location.pathname.startsWith('/course/')) {
    const courseId = window.location.pathname.split('/')[2];
    if (courseId) {
      loadStudentFiles(courseId);
    }
    return;
  }

  // Teacher file management - only if on teacher dashboard
  const teacherFileList = document.getElementById('teacherFileList');
  if (teacherFileList) {
    // Initialize teacher file management
    setupTeacherFileManagement();
  }
}


async function setupStudentUpload(courseId) {
  const form = document.getElementById('studentUploadForm');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('studentFileInput');
    
    // Add debug logs
    console.log('Upload started');
    console.log('Selected file:', fileInput.files[0]);
    console.log('Course ID:', courseId);

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('course_id', courseId);

    try {
      const response = await fetch('/upload_student_file', {
        method: 'POST',
        body: formData
      });
      
      // Add response logging
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

    } catch (error) {
      console.error('Upload error:', error);
    }
  });
}





// Teacher File Management
function setupTeacherFileUpload() {
  const courseSelect = document.getElementById('teacherCourseSelect');
  const groupSelect = document.getElementById('teacherGroupSelect');
  const daySelect = document.getElementById('teacherDaySelect');
  const filesContainer = document.getElementById('teacherFilesContainer');

  async function loadSelections() {
    try {
      // Load initial files if selections exist
      if (courseSelect.value && groupSelect.value && daySelect.value) {
        await loadTeacherFiles(courseSelect.value, daySelect.value);
      }
    } catch (e) {
      console.error('Initial load error:', e);
    }
  }

  courseSelect?.addEventListener('change', async function() {
    if (!this.value) return;
    try {
      const res = await fetch(`/get_teacher_groups/${this.value}/${document.getElementById('teacherData').dataset.teacherId}`);
      const data = await res.json();
      groupSelect.innerHTML = '<option value="">Select Group</option>';
      data.groups.forEach(group => {
        groupSelect.add(new Option(group, group));
      });
      groupSelect.disabled = false;
      filesContainer.innerHTML = '';
    } catch (e) {
      console.error('Error loading groups:', e);
    }
  });

  groupSelect?.addEventListener('change', async function() {
    if (!this.value) return;
    try {
      const res = await fetch(`/get_group_days_for_files/${courseSelect.value}/${this.value}`);
      const data = await res.json();
      daySelect.innerHTML = '<option value="">Select Day</option>';
      data.days.forEach(day => {
        daySelect.add(new Option(`Day ${day.day} - ${day.date}`, day.day));
      });
      daySelect.disabled = false;
      filesContainer.innerHTML = '';
    } catch (e) {
      console.error('Error loading days:', e);
    }
  });

  daySelect?.addEventListener('change', async function() {
    if (this.value && courseSelect.value) {
      await loadTeacherFiles(courseSelect.value, this.value);
    }
  });

  document.getElementById('teacherUploadForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData();
    formData.append('file', document.getElementById('teacherFileInput').files[0]);
    formData.append('course_id', courseSelect.value);
    formData.append('group_name', groupSelect.value);
    formData.append('day', daySelect.value);

    try {
      const res = await fetch('/upload_course_file', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        await loadTeacherFiles(courseSelect.value, daySelect.value);
      }
    } catch (e) {
      console.error('Upload error:', e);
    }
  });

  loadSelections();
}

// Student File Management
function setupStudentFileUpload() {
  const daySelect = document.getElementById('studentDaySelect');
  const courseId = window.location.pathname.split('/')[2];
  const userId = document.getElementById('userData')?.dataset.userId;
  let groupName = null;

  async function loadDays() {
    try {
      if (!userId) throw new Error('User not logged in');
      const groupRes = await fetch(`/get_student_group/${courseId}/${userId}`);
      const groupData = await groupRes.json();
      
      if (!groupData.success) throw new Error('No group found');
      groupName = groupData.group_name;

      const res = await fetch(`/get_group_days_for_files/${courseId}/${groupName}`);
      const data = await res.json();
      daySelect.innerHTML = '<option value="">Select Day</option>';

      // Add default selection
    if (data.days.length > 0) {
      data.days.forEach((day, index) => {
        const option = new Option(`Day ${day.day} - ${day.date}`, day.day);
        if (index === 0) option.selected = true; // Auto-select first day
        daySelect.add(option);
      });
      // Trigger initial load
      await loadStudentFiles(courseId, daySelect.value);
    }
  } catch (e) {
    console.error('Error loading days:', e);
  }
}

  document.getElementById('studentUploadForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    if (!daySelect.value) {
      alert('Please select a day first');
      return;
    }

    const formData = new FormData();
    formData.append('file', document.getElementById('studentFileInput').files[0]);
    formData.append('course_id', courseId);
    formData.append('group_name', groupName);
    formData.append('day', daySelect.value);

    try {
      const res = await fetch('/upload_course_file', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        await loadStudentFiles(courseId, daySelect.value);
      }
    } catch (e) {
      console.error('Upload error:', e);
    }
  });

  daySelect?.addEventListener('change', async function() {
    if (this.value) {
      await loadStudentFiles(courseId, this.value);
    }
  });

  loadDays();
}


// File Display Functions
async function loadTeacherFiles(courseId, day) {
  const container = document.getElementById('teacherFilesContainer');
  try {
    const res = await fetch(`/get_files_by_day/${courseId}/${day}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    
    const data = await res.json();
    container.innerHTML = '';
    
    data.files.forEach(file => {
      const fileCard = document.createElement('div');
      fileCard.className = 'file-card';
      fileCard.innerHTML = `
        <div class="file-card-header">
          <span class="file-name">${file.file_name}</span>
          <span class="file-type">${file.file_type.toUpperCase()}</span>
        </div>
        <div class="file-meta">
          <div>Size: ${formatFileSize(file.file_size)}</div>
          <div>Uploaded by: ${file.uploader}</div>
        </div>
        <div class="file-actions">
          <button class="download-btn" data-file="${file.file_path}" data-name="${file.file_name}">
            Download
          </button>
          <button class="delete-btn" data-id="${file.id}">
            Delete
          </button>
        </div>
      `;
      container.appendChild(fileCard);
    });
  } catch (e) {
    console.error('Error loading files:', e);
    container.innerHTML = '<p class="error">Error loading files. Please try again.</p>';
  }
}


async function loadStudentFiles(courseId, day) {
  if (!day || day === "undefined") {
    console.log('Day selection required');
    return;
  }
  const container = document.getElementById('studentFilesContainer');
  try {
    const res = await fetch(`/get_files_by_day/${courseId}/${day}`);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    
    const data = await res.json();
    container.innerHTML = '';
    
    data.files.forEach(file => {
      const fileCard = document.createElement('div');
      fileCard.className = 'file-card';
      fileCard.innerHTML = `
        <div class="file-card-header">
          <span class="file-name">${file.file_name}</span>
          <span class="file-type">${file.file_type.toUpperCase()}</span>
        </div>
        <div class="file-meta">
          <div>Size: ${formatFileSize(file.file_size)}</div>
          <div>Uploaded by: ${file.uploader}</div>
        </div>
        <div class="file-actions">
          <button class="download-btn" data-file="${file.file_path}" data-name="${file.file_name}">
            Download
          </button>
          ${!file.is_teacher_upload ? `
          <button class="delete-btn" data-id="${file.id}">
            Delete
          </button>` : ''}
        </div>
      `;
      container.appendChild(fileCard);
    });
  } catch (e) {
    console.error('Error loading files:', e);
    container.innerHTML = '<p class="error">Error loading files. Please try again.</p>';
  }
}


