/* Direct mix delivery is enabled only after mix-config.json points at a live service. */
(() => {
  'use strict';
  async function init() {
    const mix=window.NorthernDialMix,dialog=document.getElementById('nd-mix-dialog');
    if(!mix?.snapshot || !dialog || document.getElementById('nd-mix-email-form'))return;
    let config;
    try{const r=await fetch('/mix-config.json',{cache:'no-store'});if(!r.ok)return;config=await r.json();}catch(_){return;}
    if(config.enabled!==true || typeof config.endpoint!=='string' || !config.endpoint.startsWith('https://'))return;
    const fr=location.pathname.startsWith('/fr/');const text=(en,french)=>fr?french:en;
    const form=document.createElement('form');form.id='nd-mix-email-form';form.style.cssText='margin-top:20px;padding-top:18px;border-top:1px solid #bbb';
    const emailLabel=document.createElement('label');emailLabel.htmlFor='nd-mix-email';emailLabel.textContent=text('Email me this mix','Envoyez-moi ce mix');emailLabel.style.display='block';
    const email=document.createElement('input');email.id='nd-mix-email';email.type='email';email.required=true;email.autocomplete='email';email.maxLength=254;email.placeholder=text('Your email address','Votre adresse courriel');email.style.cssText='width:100%;box-sizing:border-box;padding:10px;margin:8px 0;font:inherit;border:1px solid #555;border-radius:6px';
    const optLabel=document.createElement('label');optLabel.style.cssText='display:flex;align-items:flex-start;gap:8px;font-size:14px;margin:10px 0';
    const opt=document.createElement('input');opt.type='checkbox';opt.checked=false;
    const words=document.createElement('span');words.textContent=text('Email me music recommendations and stories based on my mix.','Envoyez-moi des recommandations musicales et des articles selon mon mix.');optLabel.append(opt,words);
    const detail=document.createElement('p');detail.style.cssText='font-size:13px;color:#555';detail.textContent=text('Optional. Confirm your subscription using the link in your mix email. Unsubscribe anytime.','Facultatif. Confirmez votre inscription grâce au lien dans le courriel. Désabonnez-vous à tout moment.');
    const send=document.createElement('button');send.type='submit';send.textContent=text('Send my mix','Envoyer mon mix');
    const status=document.createElement('p');status.setAttribute('role','status');status.setAttribute('aria-live','polite');
    form.append(emailLabel,email,optLabel,detail,send,status);dialog.append(form);
    const note=dialog.querySelector('.nd-mix-note');if(note)note.textContent=text('Your mix is saved in this browser until it is sent successfully. Listening links search YouTube and Spotify. Automatic YouTube playlist creation is not available yet.','Votre mix reste enregistré jusqu’à l’envoi réussi. Les liens recherchent sur YouTube et Spotify. La création automatique de playlists YouTube n’est pas encore disponible.');
    let attempt=null,busy=false;
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(busy || !form.reportValidity())return;
      const tracks=mix.snapshot();if(!tracks.length){status.textContent=text('Add a song first.','Ajoutez d’abord une chanson.');return;}
      const payload={email:email.value.trim(),tracks,recommendations:opt.checked};
      const fingerprint=JSON.stringify(payload);
      if(attempt?.fingerprint!==fingerprint)attempt={fingerprint,id:crypto.randomUUID()};
      busy=true;send.disabled=true;email.disabled=true;opt.disabled=true;status.textContent=text('Sending your mix…','Envoi de votre mix…');
      try{
        const response=await fetch(config.endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,requestId:attempt.id}),signal:AbortSignal.timeout(30000)});
        const result=await response.json();if(!response.ok || result.accepted!==true)throw new Error(result.error||text('Send failed. Your mix is still saved.','Échec de l’envoi. Votre mix est conservé.'));
        mix.complete(tracks);email.value='';opt.checked=false;attempt=null;
        status.textContent=payload.recommendations?text('Your mix was accepted for delivery. Check your inbox and confirm if you want future recommendations.','Votre mix a été accepté pour envoi. Consultez votre boîte courriel et confirmez les recommandations.'):text('Your mix was accepted for delivery. Your saved list is cleared.','Votre mix a été accepté pour envoi. Votre liste enregistrée est effacée.');
      }catch(error){status.textContent=error.name==='TimeoutError'?text('We could not confirm the send. Your mix is still saved.','Nous n’avons pas pu confirmer l’envoi. Votre mix est conservé.'):error.message;}
      finally{busy=false;send.disabled=false;email.disabled=false;opt.disabled=false;}
    });
  }
  init();
})();
