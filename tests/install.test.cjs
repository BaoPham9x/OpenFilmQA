const {test}=require('node:test');const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const os=require('node:os');const {spawnSync}=require('node:child_process');
const cli=path.resolve(__dirname,'../bin/openfilmqa.js');
function run(cwd,args){return spawnSync(process.execPath,[cli,...args],{cwd,encoding:'utf8'});}
test('real skill installs and bundled CLI runs; existing skill is preserved',()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'filmqa-install-'));
 try {assert.equal(run(temp,['install']).status,0);const skill=path.join(temp,'.agents/skills/openfilmqa');assert.ok(fs.existsSync(path.join(skill,'SKILL.md')));
 assert.equal(spawnSync('python3',[path.join(skill,'bin/qa.py'),'--help'],{encoding:'utf8'}).status,0);
 const bytes=fs.readFileSync(path.join(skill,'SKILL.md'));assert.equal(run(temp,['install']).status,3);assert.deepEqual(fs.readFileSync(path.join(skill,'SKILL.md')),bytes);
 } finally {fs.rmSync(temp,{recursive:true,force:true});}
});
test('dry run does not write; symlink parents and destinations are refused',()=>{
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'filmqa-links-'));
 try {assert.equal(run(temp,['install','--dry-run']).status,0);assert.equal(fs.existsSync(path.join(temp,'.agents')),false);
 const target=path.join(temp,'target');fs.mkdirSync(target);fs.symlinkSync(target,path.join(temp,'.agents'));
 assert.equal(run(temp,['install']).status,3);assert.deepEqual(fs.readdirSync(target),[]);
 fs.symlinkSync(path.join(temp,'missing'),path.join(temp,'broken'));assert.equal(run(temp,['install','--dir',path.join(temp,'broken')]).status,3);
 } finally {fs.rmSync(temp,{recursive:true,force:true});}
});
