import { Capacitor, registerPlugin } from '@capacitor/core';
import {STREAM} from './content.js';
const NativeRadio = registerPlugin('NativeRadio');
export class Radio extends EventTarget {
  constructor() {
    super(); this.state = 'paused'; this.intent = false; this.native = Capacitor.isNativePlatform();
    if (!this.native) {
      this.audio = new Audio(); this.audio.preload = 'none';
      for (const [event,state] of Object.entries({playing:'playing',waiting:'buffering',pause:'paused',error:'error'})) {
        this.audio.addEventListener(event, () => this.setState(state));
      }
    }
  }
  async init() {
    if (this.native) {
      await NativeRadio.addListener('stateChange', s => this.setState(s.state));
      const s = await NativeRadio.getState(); this.setState(s.state);
    } else if ('mediaSession' in navigator) {
      navigator.mediaSession.setActionHandler('play',()=>this.play());
      navigator.mediaSession.setActionHandler('pause',()=>this.pause());
    }
  }
  setState(state) { this.state = state; this.dispatchEvent(new Event('change')); }
  async play() {
    this.intent = true; this.setState('buffering');
    try {
      if (this.native) await NativeRadio.play();
      else { this.audio.src = STREAM; await this.audio.play(); if (!this.intent) this.audio.pause(); }
    } catch { if (this.intent) this.setState('error'); }
  }
  async pause() {
    this.intent = false;
    try { if (this.native) await NativeRadio.pause(); else this.audio.pause(); this.setState('paused'); }
    catch { this.setState('error'); }
  }
  async metadata(song) {
    if (this.native) return; // Native player refreshes metadata even when WebView is suspended.
    if ('mediaSession' in navigator) navigator.mediaSession.metadata = new MediaMetadata({title:song.title || 'Northern Dial',artist:song.artist || 'Live Canadian radio',album:'Northern Dial'});
  }
}
