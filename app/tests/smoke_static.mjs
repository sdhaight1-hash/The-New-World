import assert from "node:assert/strict";
import {chromium} from "playwright";

const base=process.env.PUBLIC_SITE_URL||"http://127.0.0.1:8776/";
const browser=await chromium.launch({headless:true,...(process.env.CHROME_BIN?{executablePath:process.env.CHROME_BIN}:{})});
const page=await browser.newPage({viewport:{width:1200,height:850}});
const errors=[];
page.on("pageerror",error=>errors.push(error.message));
try{
 await page.goto(base,{waitUntil:"domcontentloaded"});
 await page.locator("#coverTitle").waitFor({state:"visible",timeout:15000});
 assert.equal(await page.locator("#studioLink").count(),0);
 const publishedCount=Number((await page.locator("#coverCount").innerText()).split(" ")[0]);
 assert.ok(publishedCount>=1,"Static reader should have at least one published article");
 assert.equal(Number(await page.locator("#coverArticleNumber").innerText()),publishedCount);
 assert.ok(await page.locator("#readingRoute .reading-route-item").count()>=1);
 assert.ok(await page.locator("#readingRoute .reading-route-item strong").first().innerText());
 await page.locator("#featuredCards .article-card").filter({hasText:"Navigation Test Settlement"}).first().click();
 await page.locator("#articleContent h1").waitFor({state:"visible"});
 assert.equal(await page.locator("#articleContent h1").innerText(),"Navigation Test Settlement");
 assert.match(await page.locator("#articleContent .reader-prose").innerText(),/Initial data entry/);
 assert.equal(await page.locator("#articleContent .archive-context strong").innerText(),"Places");
 await page.locator(".primary-nav a[href='#/browse']").click();
 await page.locator("#browseCards .article-card").filter({hasText:"Navigation Test Settlement"}).first().waitFor({state:"visible"});
 await page.locator("#searchToggle").click();
 await page.locator("#siteSearch").fill("Navigation Test");
 await page.locator("#quickResults .quick-result").first().waitFor({state:"visible"});
 await page.locator("#quickResults .quick-result").first().click();
 await page.locator("#articleContent h1").waitFor({state:"visible"});
 await page.locator("#textSettings").click();
 await page.locator("#readingAppearance").selectOption("light");
 assert.equal(await page.locator("body").getAttribute("data-appearance"),"light");
 await page.locator("#fontLarger").click();
 assert.equal(await page.locator("html").evaluate(el=>getComputedStyle(el).getPropertyValue("--read-size").trim()),"18px");
 await page.locator(".primary-nav a[href='#/history']").click();
 await page.locator("#readerHistory").waitFor({state:"visible"});
 await page.locator(".primary-nav a[href='#/atlas']").click();
 await page.locator("#readerAtlas").waitFor({state:"visible"});
 await page.setViewportSize({width:390,height:720});
 assert.equal(await page.locator("#readerAtlas").isVisible(),true);
 await page.locator(".primary-nav a[href='#/']").click();
 assert.ok(await page.locator("#readingRoute .reading-route-item").count()>=1);
 assert.deepEqual(errors,[]);
 console.log("PASS: static publication browse/article/search/theme/history/atlas/mobile (no Studio)");
}finally{
 await browser.close();
}
