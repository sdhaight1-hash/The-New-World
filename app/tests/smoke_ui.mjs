// Browser smoke test for top-level workspace identity, entry flow and contextual tools.
import assert from "node:assert/strict";
import {chromium} from "playwright";
const base=process.env.STUDIO_URL||"http://127.0.0.1:8775/app/";
const browser=await chromium.launch({headless:true, ...(process.env.CHROME_BIN?{executablePath:process.env.CHROME_BIN}:{})});
const page=await browser.newPage({viewport:{width:1440,height:900}});
const errors=[];
page.on("pageerror",error=>errors.push(error.message));
try{
 await page.goto(base,{waitUntil:"domcontentloaded"});
 await page.locator("#homeWorldTitle").waitFor({state:"visible",timeout:15000});
 assert.match(await page.locator("#spaceHeading").innerText(),/World Overview/);
 assert.equal(await page.locator("body").getAttribute("data-space"),"home");
 const nav=page.locator(".space-rail button[data-panel]");
 assert.equal(await nav.count(),6);
 for(const [space,heading] of [["article","Encyclopedia"],["timeline","Chronology"],["atlas","Historical Atlas"],["network","Connections"],["media","Media Library"],["home","World Overview"]]){
  await page.locator('.space-rail button[data-panel="'+space+'"]').click();
  assert.equal(await page.locator("body").getAttribute("data-space"),space);
  assert.equal(await page.locator("#spaceHeading").innerText(),heading);
  assert.equal(await page.locator('.space-rail button[data-panel="'+space+'"]').getAttribute("aria-current"),"page");
 }
 await page.locator("#homeNew").click();
 await page.locator("#createDialog").waitFor({state:"visible"});
 await page.locator("#createTitle").fill("Navigation Test Settlement");
 await page.locator("#createType").selectOption("place");
 await page.locator("#createForm button[type=submit]").click();
 await page.locator("#writePanel").waitFor({state:"visible"});
 assert.equal(await page.locator("#breadcrumb").innerText(),"Locations / Navigation Test Settlement");
 await page.locator("#eSummary").fill("A deliberately created sample record.");
 await page.locator("#eBody").fill("## Survey notes\nInitial data entry.");
 await page.locator('#editForm button[type=submit]').click();
 await page.locator("#notice").waitFor({state:"visible"});
 await page.locator('[data-mode=read]').click();
 await page.locator("#readPanel").waitFor({state:"visible"});
 assert.match(await page.locator("#readPanel").innerText(),/Initial data entry/);
 await page.locator('[data-mode=design]').click();
 await page.locator("#designPanel").waitFor({state:"visible"});
 await page.locator("#dTheme").selectOption("civic");
 await page.locator("#saveDesign").click();
 await page.locator('[data-mode=explore]').click();
 await page.locator("#explorePanel").waitFor({state:"visible"});
 await page.locator('.space-rail button[data-panel=home]').click();
 assert.equal(await page.locator("#homeMetrics .metric-card").count(),4);
 await page.locator('.space-rail button[data-panel=media]').click();
 await page.locator("#globalMediaGrid").waitFor({state:"visible"});
 assert.equal(errors.length,0,errors.join("\n"));
 console.log("PASS: workspace identities, navigation, create/write/read/design/explore, overview and media");
}finally{
 await browser.close();
}
