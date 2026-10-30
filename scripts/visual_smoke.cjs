// Playwright tests run locally; no comic is uploaded.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),assert=require('node:assert/strict');
(async()=>{
 const report=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);fs.mkdirSync(output,{recursive:true});
 const browser=await chromium.launch({headless:true,channel:'chrome',downloadsPath:output});
 try {
  const context=await browser.newContext({viewport:{width:1500,height:1100},acceptDownloads:true});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(pathToFileURL(report).href);await page.waitForFunction(()=>document.querySelector('#overlay').naturalWidth>0);
  const pages=await page.locator('#page option').count();assert(pages>0);
  await page.locator('#notes').fill('Test przeglądarki: kolejność 1 → 2');await page.locator('[data-issue=reviewed]').check();
  await page.reload();await page.waitForFunction(()=>document.querySelector('#overlay').naturalWidth>0);
  assert.equal(await page.locator('#notes').inputValue(),'Test przeglądarki: kolejność 1 → 2');assert(await page.locator('[data-issue=reviewed]').isChecked());
  await page.locator('#next').click();assert.equal(await page.locator('#page').inputValue(),'1');
  await page.keyboard.press('ArrowLeft');assert.equal(await page.locator('#page').inputValue(),'0');
  const pending=page.waitForEvent('download');await page.locator('#export').click();
  const download=await pending;await download.saveAs(path.join(output,'export-test.json'));
  const exported=JSON.parse(fs.readFileSync(path.join(output,'export-test.json'),'utf8'));
  assert.equal(exported.pages.length,pages);assert(exported.pages[0].review.reviewed);
  await page.locator('#page').selectOption(String(Math.min(8,pages-1)));
  await page.waitForFunction(()=>[...document.images].every(im=>im.complete&&im.naturalWidth>0));
  assert.equal(await page.evaluate(()=>scrollY),0);
  await page.screenshot({path:path.join(output,'desktop.png'),fullPage:true});
  assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
  await page.locator('#zoom').click();assert(await page.locator('body').evaluate(el=>el.classList.contains('zoom')));
  await page.setViewportSize({width:390,height:844});await page.locator('#zoom').click();
  await page.screenshot({path:path.join(output,'mobile.png'),fullPage:true});
  assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)));
  const linkedIndex=Math.min(18,pages-1);
  const linkedSha=await page.evaluate(i=>records[i].sha256.slice(0,12),linkedIndex);
  await page.goto(pathToFileURL(report).href+'#page='+linkedSha);
  await page.waitForFunction(i=>document.querySelector('#page').value===String(i),linkedIndex);
  await page.reload();
  await page.waitForFunction(i=>document.querySelector('#page').value===String(i),linkedIndex);
  await page.evaluate(()=>location.hash='#page=invalid');
  await page.waitForFunction(()=>document.querySelector('#page').value==='0');
  for(let i=0;i<pages;i++){await page.locator('#page').selectOption(String(i));await page.waitForFunction(()=>[...document.images].every(im=>im.complete&&im.naturalWidth>0));}
  assert.deepEqual(errors,[]);
  const summary={pages,checks:['all images decode','navigation','keyboard','persisted review','JSON export','zoom','desktop layout','mobile layout','direct page link','refresh linked page','invalid link fallback','no JavaScript errors']};
  fs.writeFileSync(path.join(output,'browser-tests.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify(summary));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
