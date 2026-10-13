const $ = id => document.getElementById(id);
let current = null, selected = new Set(), answered = null, currentView = 'practice';
let elapsedMs = 0, startedAt = null, loading = false;

function pauseTimer() { if(startedAt!==null){elapsedMs+=performance.now()-startedAt;startedAt=null;} }
function resumeTimer() { if(current && !answered && currentView==='practice' && !document.hidden && startedAt===null) startedAt=performance.now(); }
function answerSeconds() { pauseTimer(); return Math.min(1800,Math.max(1,Math.round(elapsedMs/1000))); }
function formatTime(seconds) { const n=Math.round(seconds); return n<60?`${n}초`:`${Math.floor(n/60)}분 ${String(n%60).padStart(2,'0')}초`; }
function inlineMarkdown(parent, text) {
  const pieces=text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
  for(const piece of pieces){
    if(piece.startsWith('**') && piece.endsWith('**'))parent.append(el('strong','',piece.slice(2,-2)));
    else if(piece.startsWith('`') && piece.endsWith('`'))parent.append(el('code','',piece.slice(1,-1)));
    else parent.append(document.createTextNode(piece));
  }
}
function renderMarkdown(body) {
  const container=el('div','explanation-body'), lines=body.replace(/\r\n?/g,'\n').split('\n');
  let paragraph=[], list=null;
  const flush=()=>{if(paragraph.length){const p=el('p');inlineMarkdown(p,paragraph.join(' '));container.append(p);paragraph=[];}};
  for(const raw of lines){
    const line=raw.trim();
    if(!line){flush();list=null;continue;}
    const heading=line.match(/^#{1,4}\s+(.+)$/);
    if(heading){flush();list=null;const h=el('h4');inlineMarkdown(h,heading[1]);container.append(h);continue;}
    const bullet=line.match(/^[-*]\s+(.+)$/);
    if(bullet){flush();if(!list){list=el('ul');container.append(list);}const item=el('li');inlineMarkdown(item,bullet[1]);list.append(item);continue;}
    list=null;paragraph.push(line);
  }
  flush();return container;
}

async function api(path, body) {
  const options = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {};
  const response = await fetch(path, options);
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  return value;
}
function el(tag, className, text) { const node=document.createElement(tag); if(className)node.className=className; if(text!==undefined)node.textContent=text; return node; }
function setView(view) {
  pauseTimer();
  currentView=view;
  for (const name of ['practice','review','guide']) $(name+'-view').classList.toggle('hidden',name!==view);
  document.querySelectorAll('.nav').forEach(button=>button.classList.toggle('active',button.dataset.view===view));
  $('page-title').textContent={practice:'오늘의 연습',review:'취약 개념',guide:'학습 안내'}[view];
  if(view==='review') refreshStats();
  resumeTimer();
}
async function refreshStats() {
  const s=await api('/api/stats');
  $('stat-total').textContent=s.total.toLocaleString(); $('stat-studied').textContent=s.studied.toLocaleString();
  $('stat-attempts').textContent=`풀이 기록 ${s.attempts}회`; $('stat-due').textContent=s.due;
  $('vault-path').textContent=`Obsidian 볼트: ${s.vault} · AI 해설: ${s.api_ready ? s.model+' 연결 준비됨' : 'API 키 설정 필요'}`;
  $('review-map-link').href=`obsidian://open?path=${encodeURIComponent(`${s.vault}/Review/00-오답-지도.md`)}`;
  const personalPace=s.timing.personal_p75_seconds===null?'개인 기준은 8회 후 반영':`시험 페이스와 내 상위 25% ${formatTime(s.timing.personal_p75_seconds)} 중 긴 시간`;
  const overallPace=s.timing.average_seconds===null?'내 평균 계산 중':`내 평균 ${formatTime(s.timing.average_seconds)} (${s.timing.samples}회)`;
  $('timing-rule').textContent=`시험 65문항·90분 ≈ ${formatTime(s.timing.exam_pace_seconds)}/문항 · ${overallPace} · 느린 기준 ${formatTime(s.timing.slow_threshold_seconds)} (${personalPace}) · 반복 3회+·오답률 40%+·문항 평균이 기준 이상일 때 표시`;
  const confusing=$('confusing-list');confusing.replaceChildren();
  if(!s.confusing_questions.length){confusing.append(el('div','empty-review','아직 분포를 판단할 만큼 반복해서 푼 문제가 없습니다. 오답은 아래 취약 개념에 바로 반영됩니다.'));}
  for(const q of s.confusing_questions){
    const item=el('article','confusing-item'), info=el('div'), title=el('strong','',`모의고사 ${q.exam} · ${q.number}번`);
    const stem=el('p','',q.stem), detail=el('span','',`${q.attempts}회 풀이 · 오답률 ${Math.round(q.wrong_rate*100)}% · 평균 ${formatTime(q.avg_seconds)}`);
    const revisit=el('button','secondary','이 문제 다시 풀기');revisit.onclick=()=>{setView('practice');loadQuestion(q.id);};
    info.append(title,stem,detail);item.append(info,revisit);confusing.append(item);
  }
  const list=$('weak-list'); list.replaceChildren();
  if(!s.weak.length){list.append(el('div','empty-review','아직 취약 개념이 없습니다. 오답이나 오래 걸린 정답이 쌓이면 여기에 나타납니다.'));return;}
  for(const concept of s.weak){
    const item=el('article','weak-item'), left=el('div'), title=el('h3','',concept.title), desc=el('p','',concept.summary);
    const link=el('a','', 'Obsidian 개념 노트 열기 ↗');link.href=`obsidian://open?path=${encodeURIComponent(`${s.vault}/Concepts/${concept.id}.md`)}`;
    left.append(title,desc,link); const count=el('div','weak-count',`${concept.weak}회 다시 보기`);count.append(el('small','',`총 ${concept.attempts}회 풀이`));item.append(left,count);list.append(item);
  }
}
function renderQuestion() {
  const card=$('question-card');card.replaceChildren();
  $('next').classList.toggle('hidden',Boolean(answered));
  $('next-dock').classList.toggle('hidden',!answered || !current);
  if(!current){card.append(el('div','loading','이 조건에 맞는 문제가 없습니다. 모드나 회차를 바꿔 보세요.'));return;}
  const top=el('div','question-top'), badge=el('span','badge',current.concept.title), no=el('span','question-no',`EXAM ${String(current.exam).padStart(2,'0')} / Q${String(current.number).padStart(2,'0')}`);
  top.append(badge,no);card.append(top);
  if(current.needs_review){card.append(el('span','badge warn','현재 AWS 공식 자료 재확인 권장'));}
  card.append(el('h3','question-text',current.stem));
  const options=el('div','option-list');
  for(const [letter,text] of Object.entries(current.options)){
    const button=el('button','option');button.type='button';button.setAttribute('aria-pressed',selected.has(letter));
    if(selected.has(letter))button.classList.add('selected');
    if(answered){if(answered.correct.includes(letter))button.classList.add('correct');else if(selected.has(letter))button.classList.add('wrong');}
    button.append(el('span','option-letter',letter),el('span','',text));
    button.addEventListener('click',()=>{if(answered)return;if(!current.multiple)selected.clear();if(selected.has(letter))selected.delete(letter);else selected.add(letter);renderQuestion();card.querySelector(`[data-letter="${letter}"]`)?.focus();});
    button.dataset.letter=letter;
    options.append(button);
  }
  card.append(options);
  if(!answered){
    const actions=el('div','question-actions'), hint=el('span','time-hint','풀이 시간 자동 기록 · 화면을 벗어난 시간은 제외'), submit=el('button','primary','정답 확인');submit.disabled=!selected.size || loading;
    submit.onclick=async()=>{if(loading)return;loading=true;submit.disabled=true;submit.textContent='채점 중…';
      try{answered=await api('/api/answer',{id:current.id,selected:[...selected],duration_seconds:answerSeconds()});renderQuestion();
        const result=card.querySelector('.result');result?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});refreshStats().catch(console.error);
      }catch(error){resumeTimer();submit.disabled=false;submit.textContent='정답 확인';alert(error.message);}finally{loading=false;}};
    actions.append(hint,submit);card.append(actions);return;
  }
  const result=el('div','result'), title=el('h3',answered.is_correct?'good':'bad',answered.is_correct?'정답입니다':'다시 살펴볼 문제입니다');
  title.tabIndex=-1;result.append(title);
  const summary=el('section','answer-summary');
  summary.append(el('span','answer-summary-label','문제은행 정답'));
  const correctChoices=el('div','answer-values');
  for(const letter of answered.correct){
    const choice=el('div','answer-value');
    choice.append(el('span','answer-letter',letter),el('strong','',current.options[letter] || letter));
    correctChoices.append(choice);
  }
  summary.append(correctChoices,el('p','answer-description',answered.offline_explanation));result.append(summary);
  const timing=answered.duration_seconds===null?'풀이 시간 미기록':`풀이 ${formatTime(answered.duration_seconds)} · 이 문제 평균 ${formatTime(answered.question_stats.avg_seconds)} (${answered.question_stats.attempts}회) · 내 전체 평균 ${formatTime(answered.personal_average_seconds)} · 느린 기준 ${formatTime(answered.time_threshold_seconds)}`;
  const interpretation=answered.is_correct?(answered.confused?'반복 오답과 평균 풀이 시간이 높아 내일 다시 봅니다.':answered.slow?'오래 걸린 정답이라 내일 다시 봅니다.':'정답을 맞혀 복습 간격이 늘어났습니다.'):'오답이라 내일 다시 봅니다.';
  const timingFeedback=el('p','timing-feedback',`${timing} · ${interpretation}`);
  const row=el('div','result-row');
  for(const source of answered.official_sources || []){
    const link=el('a','',`${source.label} ↗`);link.href=source.url;link.target='_blank';link.rel='noopener noreferrer';row.append(link);
  }
  const explanationSlot=el('div','explanation-slot');explanationSlot.setAttribute('aria-live','polite');
  const explain=el('button','secondary','AI 비교 해설 요청');explain.onclick=async()=>{const questionId=current.id,attemptId=answered.attempt_id;explain.disabled=true;explain.textContent='해설 생성 중…';
    try{const value=await api('/api/explain',{id:current.id,selected:[...selected],attempt_id:answered.attempt_id});
      const content=el('div','explanation');content.append(renderMarkdown(value.body));
      if(value.note_relative){const saved=el('p','saved-review'), link=el('a','', 'Obsidian에서 오답 노트 열기');
        link.href=`obsidian://open?path=${encodeURIComponent(value.note_path)}`;
        saved.append('저장됨 · ',link,el('span','',` ${value.note_relative}`));content.append(saved);}
      explanationSlot.replaceChildren(content);
      requestAnimationFrame(()=>{
        if(currentView==='practice' && current?.id===questionId && answered?.attempt_id===attemptId && content.isConnected && document.activeElement!==textarea)
          content.scrollIntoView({block:'start',behavior:'instant'});
      });
    }catch(error){explanationSlot.replaceChildren(el('div','explanation',error.message));}
    finally{explain.disabled=false;explain.textContent='AI 비교 해설 다시 보기';}};
  row.append(explain);result.append(row,explanationSlot,timingFeedback);
  const box=el('div','note-box'), label=el('label','', '내가 헷갈린 이유를 Obsidian에 남기기'), textarea=el('textarea');textarea.placeholder='예: CloudTrail과 CloudWatch의 역할을 반대로 기억했다.';
  const save=el('button','secondary','개념 노트에 저장');const msg=el('span','notice');
  save.onclick=async()=>{try{const r=await api('/api/save-note',{id:current.id,reason:textarea.value});msg.textContent=`저장됨: ${r.path}`;textarea.value='';}catch(error){msg.textContent=error.message;}};
  box.append(label,textarea,save,msg);result.append(box);
  card.append(result);
}
async function loadQuestion(questionId=null){
  if(loading)return;
  const shouldScroll=Boolean(current || questionId);
  loading=true;pauseTimer();
  $('next-dock').classList.add('hidden');
  $('question-card').replaceChildren(el('div','loading','문제를 불러오는 중입니다…'));
  try{const query=new URLSearchParams({mode:$('mode').value});if($('exam').value)query.set('exam',$('exam').value);
    if(questionId)query.set('id',questionId);else if(current)query.set('exclude',current.id);
    const value=await api(`/api/next?${query}`);current=value.question;selected=new Set();answered=null;elapsedMs=0;startedAt=null;renderQuestion();resumeTimer();
    if(shouldScroll)$('question-card').scrollIntoView({block:'start',behavior:'auto'});
  }catch(error){$('question-card').replaceChildren(el('div','loading',error.message));}finally{loading=false;}
}
for(let i=1;i<=23;i++){const option=el('option','',`${i}회차`);option.value=i;$('exam').append(option);}
document.querySelectorAll('.nav').forEach(button=>button.onclick=()=>setView(button.dataset.view));
$('next').onclick=()=>loadQuestion();$('next-answer').onclick=()=>loadQuestion();$('mode').onchange=()=>loadQuestion();$('exam').onchange=()=>loadQuestion();
document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseTimer();else resumeTimer();});
document.addEventListener('keydown',event=>{if(event.key.toLowerCase()==='n' && answered && currentView==='practice' && !event.repeat && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)){event.preventDefault();loadQuestion();}});
refreshStats().catch(console.error);loadQuestion();
