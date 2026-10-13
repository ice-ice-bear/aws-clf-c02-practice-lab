const $ = id => document.getElementById(id);
let current = null, selected = new Set(), answered = null, currentView = 'practice';
let elapsedMs = 0, startedAt = null, loading = false;
let session = null, adHoc = false, setupOpen = false;
let concepts = [], activeConcept = null, qaContext = null, qaResponse = null, currentAiExplanation = '';

function pauseTimer() { if(startedAt!==null){elapsedMs+=performance.now()-startedAt;startedAt=null;} }
function resumeTimer() { if(current && !answered && currentView==='practice' && !document.hidden && startedAt===null) startedAt=performance.now(); }
function answerSeconds() { pauseTimer(); return Math.min(1800,Math.max(1,Math.round(elapsedMs/1000))); }
function formatTime(seconds) { const n=Math.round(seconds); return n<60?`${n}초`:`${Math.floor(n/60)}분 ${String(n%60).padStart(2,'0')}초`; }
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
  for (const name of ['practice','concepts','review','guide']) $(name+'-view').classList.toggle('hidden',name!==view);
  document.querySelectorAll('.nav').forEach(button=>button.classList.toggle('active',button.dataset.view===view));
  $('page-title').textContent={practice:'오늘의 연습',concepts:'개념 학습',review:'취약 개념',guide:'학습 안내'}[view];
  if(view==='review') refreshStats();
  $('ask-selection').classList.add('hidden');
  resumeTimer();
}
function renderConcept(concept) {
  activeConcept=concept;qaContext=null;$('ask-selection').classList.add('hidden');
  $('concept-picker').value=concept.id;
  document.querySelectorAll('.concept-item').forEach(button=>button.classList.toggle('active',button.dataset.id===concept.id));
  const reader=$('concept-reader');reader.replaceChildren();
  const heading=el('header','concept-heading');
  const title=el('div');title.append(el('span','badge',concept.domain),el('h2','',concept.title));
  const open=el('a','secondary concept-open','Obsidian에서 열기');
  open.href=`obsidian://open?path=${encodeURIComponent(`${studyVault}/Concepts/${concept.id}.md`)}`;
  heading.append(title,open);reader.append(heading);
  const body=el('div','concept-body');body.append(renderMarkdown(concept.body));reader.append(body);
}
let studyVault = '';
async function initConcepts() {
  const value=await api('/api/study-concepts');concepts=value.concepts;
  const list=$('concept-list'),picker=$('concept-picker');list.replaceChildren();picker.replaceChildren();
  for(const domain of [...new Set(concepts.map(item=>item.domain))]){
    const group=el('div','concept-group');group.append(el('h3','',domain));
    const optionGroup=el('optgroup');optionGroup.label=domain;
    for(const concept of concepts.filter(item=>item.domain===domain)){
      const button=el('button','concept-item',concept.title);button.type='button';button.dataset.id=concept.id;
      button.onclick=()=>renderConcept(concept);group.append(button);
      const option=el('option','',concept.title);option.value=concept.id;optionGroup.append(option);
    }
    list.append(group);picker.append(optionGroup);
  }
  picker.onchange=()=>renderConcept(concepts.find(item=>item.id===picker.value));
  if(concepts.length)renderConcept(concepts[0]);
}
async function refreshStats() {
  const s=await api('/api/stats');
  studyVault=s.vault;
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
  $('ask-selection').classList.add('hidden');qaContext=null;
  renderSessionChrome();
  $('next-dock').classList.toggle('hidden',!answered || !current);
  $('next-answer').textContent=adHoc?'세트로 돌아가기':session?.position===session?.total?'결과 보기':'다음 문제';
  if(!current){
    if(session?.complete){
      const done=el('div','session-complete');done.append(el('span','badge','세트 완료'),el('h3','',`${session.total}문항을 마쳤습니다`),
        el('p','',`정답 ${session.correct}문항 · 오답 ${session.answered-session.correct}문항 · 건너뜀 ${session.skipped}문항. 오답과 풀이 시간은 취약 개념에 반영되었습니다.`));
      const action=el('button','primary','새 세트 고르기');action.onclick=()=>{setupOpen=true;renderSessionChrome();refreshSessionList();$('session-setup').scrollIntoView({block:'start'});};done.append(action);card.append(done);
    }else card.append(el('div','loading','풀이 방식을 선택해 세트를 시작하세요.'));
    return;
  }
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
      try{answered=await api('/api/answer',{id:current.id,selected:[...selected],duration_seconds:answerSeconds(),
        ...(session && !adHoc ? {session_id:session.id} : {})});
        if(session && !adHoc){session.answered++;if(answered.is_correct)session.correct++;}
        renderQuestion();
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
      currentAiExplanation=value.body;
      const content=el('div','explanation explanation-context');content.append(renderMarkdown(value.body));
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
function sessionLabel(value) {
  if(value.kind==='exam')return `${value.exam}회차 모의고사`;
  return {balanced:'시험 비중 랜덤',due:'복습 예정',all:'전체 문제'}[value.kind];
}
function renderSessionChrome() {
  $('session-setup').classList.toggle('hidden',!setupOpen);
  $('resume-session').classList.toggle('hidden',!session || session.complete);
  $('session-bar').classList.toggle('hidden',!session || adHoc);
  if(session && !adHoc){
    $('session-name').textContent=sessionLabel(session);
    $('session-count').textContent=session.complete?`${session.answered}문항 풀이 완료`:`${session.position} / ${session.total} · ${session.answered}문항 풀이`;
    $('progress-fill').style.width=`${100*(session.complete?session.total:session.position-1)/session.total}%`;
  }
  $('next').classList.toggle('hidden',Boolean(answered) || !current || adHoc || session?.complete);
}
function updateSetup() {
  const kind=$('session-kind').value;
  $('exam-field').classList.toggle('hidden',kind!=='exam');
  $('session-help').textContent={
    exam:'원본 모의고사 순서대로 풉니다. 이 문제은행은 공식 기출이 아닌 제3자 연습 자료입니다.',
    balanced:'공식 시험과 같은 65문항을 CLF-C02 영역 비중 24% · 30% · 34% · 12%에 가깝게 섞습니다. 영역 분류는 근사치입니다.',
    due:'오늘 복습할 문제를 모두 한 세트로 묶습니다.',
    all:'문제은행 전체를 회차 순서대로 풉니다. 언제든 중단하고 이어서 풀 수 있습니다.'
  }[kind];
}
async function refreshSessionList() {
  const value=await api('/api/sessions'), list=$('recent-session-list');list.replaceChildren();
  $('recent-sessions').classList.toggle('hidden',!value.sessions.length);
  for(const previous of value.sessions){
    const row=el('div','recent-session'), detail=el('div');
    detail.append(el('strong','',sessionLabel(previous)),
      el('span','',`${new Date(previous.created_at).toLocaleDateString('ko-KR')} · ${previous.answered}/${previous.total}문항 풀이${previous.complete?' · 완료':''}`));
    const open=el('button','secondary',previous.id===session?.id?'현재 세트':'이어 풀기');
    open.onclick=()=>loadSession(previous.id);
    row.append(detail,open);list.append(row);
  }
}
function applySession(value, shouldScroll=false) {
  pauseTimer();session=value;adHoc=false;setupOpen=!session;current=session?.question || null;
  selected=new Set();answered=null;currentAiExplanation='';elapsedMs=0;startedAt=null;renderQuestion();resumeTimer();
  if(shouldScroll)$('question-card').scrollIntoView({block:'start',behavior:'auto'});
}
async function loadSession(sessionId=null) {
  if(loading)return;loading=true;
  try{const value=sessionId?await api('/api/session/activate',{id:sessionId}):await api('/api/session');
    applySession(value.session,Boolean(sessionId));
    if(setupOpen)await refreshSessionList();}
  catch(error){$('question-card').replaceChildren(el('div','loading',error.message));}
  finally{loading=false;}
}
async function startSession() {
  if(loading)return;loading=true;$('session-error').textContent='';$('start-session').disabled=true;
  const kind=$('session-kind').value;
  try{const value=await api('/api/session',{kind,
    ...(kind==='exam'?{exam:Number($('exam').value)}:{})});
    applySession(value.session,true);
  }catch(error){$('session-error').textContent=error.message;}
  finally{loading=false;$('start-session').disabled=false;}
}
async function advanceQuestion() {
  if(loading)return;
  if(adHoc){await loadSession();return;}
  if(!session || !current)return;
  loading=true;pauseTimer();$('next-dock').classList.add('hidden');
  const questionId=current.id;
  try{const value=await api('/api/session/advance',{session_id:session.id,question_id:questionId});
    applySession(value.session,true);
  }catch(error){resumeTimer();alert(error.message);}
  finally{loading=false;}
}
async function loadQuestion(questionId){
  if(loading)return;loading=true;pauseTimer();
  try{const value=await api(`/api/next?id=${encodeURIComponent(questionId)}`);
    adHoc=true;current=value.question;selected=new Set();answered=null;currentAiExplanation='';elapsedMs=0;startedAt=null;
    renderQuestion();resumeTimer();$('question-card').scrollIntoView({block:'start',behavior:'auto'});
  }catch(error){$('question-card').replaceChildren(el('div','loading',error.message));}
  finally{loading=false;}
}
function captureStudySelection() {
  const selection=document.getSelection();
  if(!selection || selection.isCollapsed || !selection.rangeCount){$('ask-selection').classList.add('hidden');return;}
  const range=selection.getRangeAt(0), node=range.commonAncestorContainer;
  const target=node.nodeType===Node.TEXT_NODE?node.parentElement:node;
  const text=selection.toString().trim();
  if(text.length<2){$('ask-selection').classList.add('hidden');return;}
  if(currentView==='concepts' && activeConcept && $('concept-reader').contains(target)){
    qaContext={kind:'concept',id:activeConcept.id,selection:text.slice(0,4000)};
    $('ask-selection').textContent='선택 문장 AI에게 질문';$('ask-selection').classList.remove('hidden');return;
  }
  const explanation=target.closest?.('.answer-summary, .explanation-context');
  if(currentView==='practice' && answered && current && explanation){
    const ai=Boolean(explanation.closest('.explanation-context'));
    qaContext={kind:'explanation',id:current.id,source:ai?'ai':'source',selection:text.slice(0,4000),ai_context:currentAiExplanation};
    $('ask-selection').textContent='선택한 해설에 추가 질문';$('ask-selection').classList.remove('hidden');return;
  }
  $('ask-selection').classList.add('hidden');
}
function openStudyQuestion() {
  if(!qaContext)return;
  const explanation=qaContext.kind==='explanation';
  $('qa-eyebrow').textContent=explanation?'EXPLANATION Q&A':'CONCEPT Q&A';
  $('qa-title').textContent=explanation?'선택한 해설에 추가 질문':'선택한 내용 질문하기';
  $('qa-question').placeholder=explanation?'예: 이 설명은 다른 보기와 어떻게 구별되나요?':'예: 이 개념은 시험에서 어떤 보기와 자주 헷갈리나요?';
  $('qa-selection').textContent=qaContext.selection;
  $('qa-question').value='';$('qa-question').disabled=false;$('qa-status').textContent='';
  $('qa-ask').disabled=false;
  $('qa-answer').replaceChildren();$('qa-answer').classList.add('hidden');$('qa-save-row').classList.add('hidden');
  $('qa-save').disabled=false;$('qa-save').textContent='질문과 답변을 Obsidian에 저장';qaResponse=null;
  $('concept-qa-dialog').showModal();$('qa-question').focus();
}
async function askStudyQuestion() {
  const question=$('qa-question').value.trim();
  if(!question){$('qa-status').textContent='질문을 입력하세요.';return;}
  const button=$('qa-ask');button.disabled=true;button.textContent='답변 생성 중…';$('qa-status').textContent='';
  try{
    const concept=qaContext.kind==='concept';
    const endpoint=concept?'/api/ask-concept':'/api/ask-explanation';
    const payload=concept?{concept_id:qaContext.id,selection:qaContext.selection,question}:
      {id:qaContext.id,selection:qaContext.selection,question,ai_context:qaContext.ai_context};
    qaResponse=await api(endpoint,payload);
    $('qa-answer').replaceChildren(renderMarkdown(qaResponse.body));$('qa-answer').classList.remove('hidden');
    $('qa-save-row').classList.remove('hidden');$('qa-question').disabled=true;
  }catch(error){$('qa-status').textContent=error.message;}
  finally{button.disabled=Boolean(qaResponse);button.textContent='AI에게 질문';}
}
async function saveStudyQuestion() {
  if(!qaResponse || !qaContext)return;
  const button=$('qa-save');button.disabled=true;$('qa-status').textContent='';
  try{
    const value=await api('/api/save-study-qa',{
      kind:qaContext.kind,id:qaContext.id,source:qaContext.source||'concept',selection:qaContext.selection,
      question:$('qa-question').value.trim(),answer:qaResponse.body,model:qaResponse.model,
    });
    $('qa-status').textContent=`Obsidian 저장 완료 · ${value.relative}`;button.textContent='저장됨';
  }catch(error){$('qa-status').textContent=error.message;button.disabled=false;}
}
for(let i=1;i<=23;i++){const option=el('option','',`${i}회차`);option.value=i;$('exam').append(option);}
document.querySelectorAll('.nav').forEach(button=>button.onclick=()=>setView(button.dataset.view));
$('ask-selection').onclick=openStudyQuestion;$('qa-ask').onclick=askStudyQuestion;$('qa-save').onclick=saveStudyQuestion;
document.addEventListener('selectionchange',captureStudySelection);
$('concept-qa-dialog').addEventListener('close',()=>{qaContext=null;$('ask-selection').classList.add('hidden');document.getSelection()?.removeAllRanges();});
$('next').onclick=advanceQuestion;$('next-answer').onclick=advanceQuestion;
$('session-kind').onchange=updateSetup;$('start-session').onclick=startSession;
$('new-session').onclick=()=>{setupOpen=true;renderSessionChrome();refreshSessionList().catch(console.error);$('session-setup').scrollIntoView({block:'start'});};
$('resume-session').onclick=()=>{setupOpen=false;renderSessionChrome();$('question-card').scrollIntoView({block:'start'});};
document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseTimer();else resumeTimer();});
document.addEventListener('keydown',event=>{if(event.key.toLowerCase()==='n' && answered && currentView==='practice' && !event.repeat && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)){event.preventDefault();advanceQuestion();}});
updateSetup();Promise.all([refreshStats().then(initConcepts),loadSession()]).catch(console.error);
