// Antipatrón intencional: UI, estado, peticiones y reglas juntos en un solo archivo.
var allTasks = [];
var list = document.getElementById('tasks');
var msg = document.getElementById('message');

function drawTasks() {
  list.innerHTML = '';
  if (allTasks.length === 0) list.textContent = 'Todavía no existen tareas.';
  allTasks.forEach(function(task) {
    var row = document.createElement('article');
    row.className = 'task';
    var label = document.createElement('span');
    label.textContent = task.title;
    row.appendChild(label);
    var edit = document.createElement('button');
    edit.type = 'button';
    edit.className = 'edit';
    edit.textContent = 'Editar';
    edit.addEventListener('click', function() { showEditor(task, row); });
    row.appendChild(edit);
    var pill = document.createElement('small');
    pill.textContent = 'Pendiente';
    row.appendChild(pill);
    list.appendChild(row);
  });
  document.getElementById('count').textContent = allTasks.length;
}

function showEditor(task, row) {
  var editor = document.createElement('form');
  editor.className = 'edit-form';
  var input = document.createElement('input');
  input.value = task.title;
  input.maxLength = 220;
  input.setAttribute('aria-label', 'Nuevo título de la tarea');
  var save = document.createElement('button');
  save.type = 'submit';
  save.textContent = 'Guardar';
  editor.appendChild(input);
  editor.appendChild(save);
  row.replaceChildren(editor);
  input.focus();
  editor.addEventListener('submit', function(e) {
    e.preventDefault();
    fetch('/api/tasks/' + task.id, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title: input.value})
    }).then(function(r) {
      return r.json().then(function(data) {
        if (!r.ok) throw new Error(data.error || data.message || 'No se pudo guardar');
        return data;
      });
    }).then(function() {
      msg.textContent = 'Tarea actualizada';
      load();
    }).catch(function(error) { msg.textContent = error.message; });
  });
}

function load() {
  fetch('/api/tasks').then(function(r) { return r.json(); }).then(function(data) {
    allTasks = data;
    drawTasks();
  }).catch(function() { msg.textContent = 'Error cargando tareas'; });
}

document.getElementById('newTask').addEventListener('submit', function(e) {
  e.preventDefault();
  var inp = document.getElementById('title');
  fetch('/api/tasks', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({title: inp.value})
  }).then(function(r) { return r.json(); }).then(function() {
    inp.value = '';
    msg.textContent = 'Tarea creada';
    load();
  }).catch(function() { msg.textContent = 'Error creando tarea'; });
});
load();
