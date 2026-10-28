"""Verify synthetic workbench contracts in an isolated browser, never a user profile."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode, urlparse


def run(args):
    from playwright.sync_api import sync_playwright
    address=urlparse(args.base_url)
    if address.hostname not in ('127.0.0.1','localhost') or address.scheme!='http':
        raise ValueError('Use a local HTTP harness URL, not a production site')
    def visit(page,route,**params):
        page.goto(args.base_url+'/?'+urlencode(dict(t='quiet-light',sb='collapsed',r=route,**params)))
        page.locator('h1,h2').first.wait_for()
        assert page.evaluate('Array.isArray(window.__harnessRequests)'), 'Synthetic harness marker missing'
    results={}
    with sync_playwright() as playwright:
        options={'headless':True}
        executable=args.browser_executable
        if not executable and os.name=='nt':
            candidate=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe'
            if candidate.is_file():executable=str(candidate)
        if executable:options['executable_path']=executable
        browser=playwright.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
        if args.section in ('all','errors'):
            visit(page,'/listing',emagerror='validation')
            page.get_by_role('button',name='起草',exact=True).click()
            page.get_by_role('textbox',name='草稿内容').fill('Synthetic draft only')
            page.get_by_role('button',name='保存本地草稿',exact=True).click()
            page.get_by_role('alert').filter(has_text='Synthetic invalid value').wait_for()
            visit(page,'/emag',emagerror='validation')
            page.get_by_role('button',name='查看 / 记录',exact=True).click()
            page.get_by_role('textbox',name='处理说明').fill('Synthetic record only')
            page.get_by_role('button',name='保存本地记录',exact=True).click()
            page.get_by_role('alert').filter(has_text='Synthetic invalid value').wait_for()
            results['validation_errors_render_as_text']=True
        if args.section in ('all','stock'):
            visit(page,'/tools',stockcase='invalid')
            page.get_by_text('\u5e93\u5b58\u672a\u77e5 4 \u6761',exact=False).wait_for()
            results['stock_unknown_matches_summary']=True
        if args.section in ('all','catalog'):
            visit(page,'/dashboard')
            page.keyboard.press('Control+k')
            dialog=page.get_by_role('dialog',name='全部工具',exact=True);dialog.wait_for()
            assert dialog.locator('.tv-card').filter(has_text='待审批').count()==1
            assert dialog.locator('.tv-card').filter(has_text='服务器终端').count()==0
            dialog.get_by_role('button',name='高级工具',exact=True).click()
            dialog.locator('.tv-card').filter(has_text='服务器终端').wait_for()
            dialog.get_by_role('textbox',name='搜索板块').fill('待审批')
            page.keyboard.press('Enter')
            page.get_by_role('heading',name='eMAG 本地方案待审批',exact=True).wait_for()
            page.set_viewport_size({'width':390,'height':1000})
            visit(page,'/dashboard',open='tools')
            page.get_by_role('dialog',name='全部工具',exact=True).wait_for()
            assert page.evaluate('document.documentElement.scrollWidth')<=390
            results['catalog_search_keyboard_mobile']=True
        if args.section in ('all','locale'):
            context=browser.new_context()
            context.add_init_script("localStorage.setItem('ivyea_ops_lang','unsupported-language')")
            localized=context.new_page();localized.on('pageerror',lambda exc:errors.append(str(exc)))
            visit(localized,'/dashboard')
            localized.get_by_text('Demo product',exact=False).wait_for()
            result=localized.evaluate('''async()=>{
              const url=performance.getEntriesByType('resource').map(x=>x.name).find(x=>x.includes('/src/api/client.ts'));
              if(!url)throw new Error('Harness API module URL not found');
              const prefix=url.slice(0,url.indexOf('/api/client.ts'));
              const {default:i18n}=await import(prefix+'/agents/i18n/config.js');
              const {api}=await import(url);
              const initial=i18n.language;
              await i18n.changeLanguage('en-US');const en=i18n.t('buttons.cancel');
              const a=(await api.get('/emag/stores/demo-ro/workspace')).data;
              await i18n.changeLanguage('zh-CN');const zh=i18n.t('buttons.cancel');
              const b=(await api.get('/emag/stores/demo-ro/workspace')).data;
              await i18n.changeLanguage('unsupported-test');
              return {initial,en,zh,fallback:i18n.t('buttons.cancel'),equivalent:JSON.stringify(a)===JSON.stringify(b)};
            }''')
            assert result=={'initial':'zh-CN','en':'Cancel','zh':'取消','fallback':'Cancel','equivalent':True},result
            results['locale_fallback_and_equivalent_evidence']=True
            context.close()
        assert not errors,errors
        browser.close()
    print(json.dumps(results,ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:5199')
    parser.add_argument('--browser-executable')
    parser.add_argument('--section',choices=('all','catalog','errors','locale','stock'),default='all')
    run(parser.parse_args())
