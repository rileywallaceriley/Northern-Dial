/* Generate the enrichment queue from the actual ranking engine, not bio length. */
const fs = require('node:fs');
const path = require('node:path');
const engine = require('../discover-engine.js');
const root = path.resolve(__dirname, '..');
const library = JSON.parse(fs.readFileSync(path.join(root, 'discovery-data.json'))).artists.map(engine.prepare);
const reportPath = path.join(root, 'data/discovery-quality.json');
const report = JSON.parse(fs.readFileSync(reportPath));
const counts = library.map(a => ({name:a.name, matches:engine.rank(library,{taste:engine.resolve(library,a.name)}).length}));
report.profilesWithMatches = counts.filter(a=>a.matches>0).length;
report.profilesWithFiveMatches = counts.filter(a=>a.matches===5).length;
report.profilesWithoutMatches = counts.filter(a=>a.matches===0).length;
report.needsEnrichment = counts.filter(a=>a.matches<5);
fs.writeFileSync(reportPath, JSON.stringify(report,null,2)+'\n');
console.log(`Discovery audit: ${report.artists} profiles, ${report.automaticRelationships} extracted relationships, ${report.profilesWithMatches} profiles with matches, ${report.profilesWithFiveMatches} with five.`);
