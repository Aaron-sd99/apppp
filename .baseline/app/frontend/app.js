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
    var pill = document.createElement('small');
    pill.textContent = 'Pendiente';
    row.appendChild(pill);
    list.appendChild(row);
  });
  document.getElementById('count').textContent = allTasks.length;
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
