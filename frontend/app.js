async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  if (!res.ok) {
    let msg = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      msg = data?.detail || JSON.stringify(data);
    } catch (_) {
      // ignore
    }
    throw new Error(msg);
  }
  return res.json();
}

function formToBody(form) {
  const formData = new FormData(form);
  const obj = {};
  for (const [k, v] of formData.entries()) obj[k] = v;

  // Coerce numeric fields (backend expects numbers)
  const numFields = [
    'Hours_Studied',
    'Attendance',
    'Sleep_Hours',
    'Previous_Scores'
  ];
  for (const f of numFields) {
    if (obj[f] !== undefined) obj[f] = Number(obj[f]);
  }

  if (obj['Tutoring_Sessions'] !== undefined) obj['Tutoring_Sessions'] = Number(obj['Tutoring_Sessions']);

  return obj;
}

function getVal(input) {
  return input.value;
}

const predictForm = document.getElementById('predictForm');
const predictResult = document.getElementById('predictResult');

predictForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  predictResult.textContent = 'Predicting...';

  try {
    const body = formToBody(predictForm);
    const data = await api('/predict', {
      method: 'POST',
      body: JSON.stringify(body)
    });

    predictResult.textContent = `Predicted Final Exam Score: ${data.predicted_score}`;
  } catch (err) {
    predictResult.textContent = `Error: ${err.message}`;
  }
});

const createForm = document.getElementById('createForm');
const crudMessage = document.getElementById('crudMessage');

createForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  crudMessage.textContent = 'Creating student...';

  try {
    const body = formToBody(createForm);
    await api('/students', { method: 'POST', body: JSON.stringify(body) });
    crudMessage.textContent = 'Created. Refreshing list...';
    await refreshStudents();
    crudMessage.textContent = 'Created.';
    createForm.reset();
  } catch (err) {
    crudMessage.textContent = `Error: ${err.message}`;
  }
});

async function refreshStudents() {
  const tbody = document.getElementById('studentsTbody');
  tbody.innerHTML = '';

  const list = await api('/students?limit=100&skip=0');
  for (const s of list) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>${s.Hours_Studied}</td>
      <td>${s.Attendance}</td>
      <td>${s.Parental_Involvement}</td>
      <td>${s.Access_to_Resources}</td>
      <td>${s.Extracurricular_Activities}</td>
      <td>${s.Sleep_Hours}</td>
      <td>${s.Previous_Scores}</td>
      <td>${s.Motivation_Level}</td>
      <td>${s.Internet_Access}</td>
      <td>${s.Tutoring_Sessions}</td>
      <td class="actions"></td>
    `;

    const actionsTd = tr.querySelector('.actions');

    const editBtn = document.createElement('button');
    editBtn.className = 'small';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => startInlineEdit(tr, s.id));

    const delBtn = document.createElement('button');
    delBtn.className = 'small danger';
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', async () => {
      try {
        crudMessage.textContent = `Deleting student ${s.id}...`;
        await api(`/students/${s.id}`, { method: 'DELETE' });
        await refreshStudents();
        crudMessage.textContent = 'Deleted.';
      } catch (err) {
        crudMessage.textContent = `Error: ${err.message}`;
      }
    });

    actionsTd.appendChild(editBtn);
    actionsTd.appendChild(delBtn);

    tbody.appendChild(tr);
  }
}

function startInlineEdit(tr, id) {
  // Simple prompt-based editor (keeps UI minimal)
  const current = {
    Hours_Studied: tr.children[1].textContent,
    Attendance: tr.children[2].textContent,
    Parental_Involvement: tr.children[3].textContent,
    Access_to_Resources: tr.children[4].textContent,
    Extracurricular_Activities: tr.children[5].textContent,
    Sleep_Hours: tr.children[6].textContent,
    Previous_Scores: tr.children[7].textContent,
    Motivation_Level: tr.children[8].textContent,
    Internet_Access: tr.children[9].textContent,
    Tutoring_Sessions: tr.children[10].textContent
  };

  const newVal = (label, oldValue) => {
    const v = window.prompt(label, oldValue);
    return v === null ? oldValue : v;
  };

  const body = {
    Hours_Studied: Number(newVal('Hours_Studied', current.Hours_Studied)),
    Attendance: Number(newVal('Attendance', current.Attendance)),
    Parental_Involvement: String(newVal('Parental_Involvement', current.Parental_Involvement)),
    Access_to_Resources: String(newVal('Access_to_Resources', current.Access_to_Resources)),
    Extracurricular_Activities: String(newVal('Extracurricular_Activities', current.Extracurricular_Activities)),
    Sleep_Hours: Number(newVal('Sleep_Hours', current.Sleep_Hours)),
    Previous_Scores: Number(newVal('Previous_Scores', current.Previous_Scores)),
    Motivation_Level: String(newVal('Motivation_Level', current.Motivation_Level)),
    Internet_Access: String(newVal('Internet_Access', current.Internet_Access)),
    Tutoring_Sessions: Number(newVal('Tutoring_Sessions', current.Tutoring_Sessions))
  };

  (async () => {
    try {
      crudMessage.textContent = `Updating student ${id}...`;
      await api(`/students/${id}`, { method: 'PUT', body: JSON.stringify(body) });
      crudMessage.textContent = 'Updated. Refreshing...';
      await refreshStudents();
      crudMessage.textContent = 'Updated.';
    } catch (err) {
      crudMessage.textContent = `Error: ${err.message}`;
    }
  })();
}

document.getElementById('refreshBtn').addEventListener('click', async () => {
  try {
    crudMessage.textContent = 'Loading students...';
    await refreshStudents();
    crudMessage.textContent = '';
  } catch (err) {
    crudMessage.textContent = `Error: ${err.message}`;
  }
});

// Initial load
refreshStudents().catch((e) => {
  crudMessage.textContent = `Error: ${e.message}`;
});

