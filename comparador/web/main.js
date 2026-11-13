const $ = id => document.getElementById(id);
let state = null;
let selected = '';
const el = (tag,cls='',content='') => {let n=document.createElement(tag);if(cls)n.className=cls;n.textContent=String(content??'');return n;};

async function refresh(){
  try{
    let response = await fetch('/api/state',{cache:'no-store'});
    if(!response.ok)throw new Error('HTTP '+response.status);
    state=await response.json();
    $('changed').textContent=state.changed;
    $('lines').textContent=`+${state.added} añadidas · −${state.removed} eliminadas`;
    $('changeStatus').textContent=state.changed?`${state.changed} archivo(s) con cambios`:'Sin modificaciones';
    const v=state.verification;
    if(v?.stale){
      $('percentage').textContent='—';$('verifyNote').textContent='Las pruebas corresponden a código anterior';
      $('apiState').textContent='Pruebas desactualizadas';$('apiState').className='verify stale';
      $('uiState').textContent='Ejecuta python check.py otra vez';
    }else if(!v){
      $('percentage').textContent='—';$('verifyNote').textContent='Ejecuta python check.py';
      $('apiState').textContent='Sin pruebas';$('apiState').className='verify';
      $('uiState').textContent='Interfaz sin verificar';
    }else{
      $('percentage').innerHTML=`${v.percent}<small>%</small>`;
      $('verifyNote').textContent=`${v.verified_count}/10 funcionalidades · ${new Date(v.timestamp).toLocaleString('es')}`;
      const r=v.requirements||{};
      $('apiState').textContent=r.R03_API?'R03 API correcta':'R03 API pendiente';
      $('apiState').className='verify '+(r.R03_API?'good':'bad');
      $('uiState').textContent=r.R03_UI_confirmada?'UI confirmada (declaración)':'UI sin verificar';
    }
    showFiles();
  }catch(e){ $('changeStatus').textContent='No se pudo actualizar: '+e.message; }
}
function showFiles(){
  $('fileCount').textContent=state.files.length;
  const container=$('files');container.replaceChildren();
  if(!state.files.length){container.append(el('p','files-empty','No se encontraron archivos'));return;}
  if(!state.files.some(f=>f.path===selected))selected=state.files.find(f=>f.status!=='sin cambios')?.path||state.files[0].path;
  for(const f of state.files){
    const b=el('button','file-btn'+(f.path===selected?' active':''));b.type='button';
    b.append(el('span','file-path',f.path));
    const more=el('div','file-info');more.append(el('span','',f.status));more.append(el('span','plus','+'+f.plus));more.append(el('span','minus','−'+f.minus));b.append(more);
    b.addEventListener('click',()=>{selected=f.path;showFiles();showDiff(f.path);});
    container.append(b);
  }
  showDiff(selected);
}
async function showDiff(path){
  $('fileName').textContent=path;
  const pane=$('diff');pane.replaceChildren(el('div','empty','Cargando comparación...'));
  try{
    let result=await fetch('/api/diff?file='+encodeURIComponent(path));
    if(!result.ok)throw new Error('No se pudo abrir el diff');
    let data=await result.json();
    pane.replaceChildren();
    if(!data.rows.length){pane.append(el('div','empty','El archivo está vacío'));return;}
    for(const row of data.rows){
      let container=el('div','diff-row '+row.kind);
      const left=el('div','line');left.append(el('span','line-no',row.bl??''),el('span','code',row.before));
      const right=el('div','line');right.append(el('span','line-no',row.al??''),el('span','code',row.after));
      container.append(left,right);pane.append(container);
    }
  }catch(e){pane.replaceChildren(el('div','empty',e.message));}
}
$('refresh').addEventListener('click',refresh);
refresh();
