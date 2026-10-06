#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
function exists(p) { try {return fs.lstatSync(p);} catch(e) {if(e.code === 'ENOENT') return null; throw e;} }
function install(options) {
 let global = false, claude = false, dry = false, dir;
 for(let i=0;i<options.length;i++) {
  const option=options[i];
  if(option==='--global') global=true;
  else if(option==='--claude') claude=true;
  else if(option==='--dry-run') dry=true;
  else if(option==='--dir' && options[i+1]) dir=options[++i];
  else throw new Error('Unknown install option: '+option);
 }
 if(dir && (global || claude)) throw new Error('Use --dir alone or a standard location.');
 const dest=path.resolve(dir || path.join(global ? os.homedir() : process.cwd(), claude ? '.claude' : '.agents','skills','openfilmqa'));
 if(exists(dest)) throw new Error('Skill folder already exists; keep it intact and choose a new --dir.');
 for(let parent=path.dirname(dest);;) {
  const stat=exists(parent);
  if(stat && (stat.isSymbolicLink() || !stat.isDirectory())) throw new Error('Skill parent must be a real directory, not a symlink or file.');
  const next=path.dirname(parent); if(next===parent) break; parent=next;
 }
 if(dry) { console.log('Would install OpenFilmQA at '+dest); return; }
 fs.mkdirSync(path.dirname(dest),{recursive:true}); fs.mkdirSync(dest);
 for(const name of ['SKILL.md','README.md','LICENSE']) fs.copyFileSync(path.join(root,name),path.join(dest,name));
 for(const folder of ['openfilmqa','docs','adapters','schemas']) {
  fs.mkdirSync(path.join(dest,folder));
  for(const name of fs.readdirSync(path.join(root,folder))) {
   if(!/\.(py|md|json)$/.test(name)) continue;
   fs.copyFileSync(path.join(root,folder,name),path.join(dest,folder,name));
  }
 }
 fs.mkdirSync(path.join(dest,'bin')); fs.copyFileSync(path.join(root,'bin','qa.py'),path.join(dest,'bin','qa.py'));
 console.log('OpenFilmQA installed at '+dest+'\nRead SKILL.md. Python 3.10+ is required for QA commands; FFmpeg is required only for media packets.');
}
try {
 if(args[0]==='install') install(args.slice(1));
 else if(!args.length) console.log('OpenFilmQA\n  openfilmqa install [--claude | --global | --dir PATH] [--dry-run]\n  openfilmqa prepare|review|judge|compare|evaluate --help\nNo reviewer is called unless judge --run is explicitly used.');
 else {
  const result=spawnSync(process.env.OPENFILMQA_PYTHON || 'python3',[path.join(root,'bin','qa.py'),...args],{stdio:'inherit'});
  if(result.error) throw new Error('Python 3.10+ is required. Set OPENFILMQA_PYTHON to its executable path.');
  process.exitCode=result.status ?? 3;
 }
} catch(e) {console.error('OpenFilmQA: '+e.message);process.exitCode=3;}
