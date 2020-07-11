#! /home/linuxbrew/.linuxbrew/bin/python3
import os, subprocess, sys

WEBVIEW_DROID = 'SYSTEM'
WEBVIEW_V5 = 'V5'


def webview_cts_v5():
    '''
    对 v5 内核进行 webview cts 测试
    '''
    cts_set_webview_type(WEBVIEW_V5)
    webview_cts_run()
    pass


def webview_cts_droid():
    '''
    对 system 内核进行 webview cts 测试
    '''
    cts_set_webview_type(WEBVIEW_DROID)
    webview_cts_run()
    cts_set_webview_type(WEBVIEW_V5)
    pass


def webview_cts_run():
    '''
    对 cts 测试开始
    1. 编译
    2. 测试
    '''
    V5_SDK_PATH = os.environ.get('V5_SDK_PATH')
    if V5_SDK_PATH != None:

        V5_CHROMIUM_PATH = f'{os.path.dirname(V5_SDK_PATH)}/android_packages_apps_Browser_chromium62'

        if not os.path.exists(V5_CHROMIUM_PATH):
            print('set v5sdk project and chromium project in the same dir!')
            exit(0)
        
        CTS_RESULT_PATH = f'{os.path.abspath(os.path.dirname(__file__))}/cts-result.txt'
        print('V5_SDK_PATH', V5_SDK_PATH)
        print('V5_CHROMIUM_PATH', V5_CHROMIUM_PATH)
        print('CTS_RESULT_PATH', CTS_RESULT_PATH)
    else:
        print('export V5_SDK_PATH to bashrc!')
        exit(1)

    # build java
    JAVA_BUILD_COMMAND = f'./tools/build.sh java'
    p = subprocess.Popen(JAVA_BUILD_COMMAND, shell=True, cwd=V5_CHROMIUM_PATH)
    p.wait()
    
    if p.returncode != 0:
        print('build java error, fix bugs first!')
        exit(1)

    # run webview-cts test
    CTS_TEST_COMMAND = f'./tools/webview-cts.sh > ~/桌面/cts-result.txt'
    p = subprocess.Popen(CTS_TEST_COMMAND, shell=True ,cwd=V5_CHROMIUM_PATH)
    p.wait()
    if p.returncode != 0:
        print('webview-cts error!')
        exit(1)

    with open(CTS_RESULT_PATH) as f:
        size=f.seek(0,2) 
        if size < 100:
            logs = f.read()
        else:
            f.seek(size-200, 0)
            logs = f.read()

    if 'OK (181 tests)' in logs:
        print(f'webview cts passed! result logs @ {CTS_RESULT_PATH}')  
    else:
        print(f'webview cts failed! see result logs @ {CTS_RESULT_PATH}')


def cts_set_webview_type(typestr):
    '''
    针对不同的内核，修改 cts 中导入内核的代码片段
    '''
    def replace_webview_inner(path, typestr):
        '''
        开始修改 load webview core type
        '''
        import fileinput

        if typestr == WEBVIEW_DROID:
            target = f'V5Loader.loadV5(this, V5Loader.CoreType.V5'
        elif typestr == WEBVIEW_V5:
            target = f'V5Loader.loadV5(this, V5Loader.CoreType.SYSTEM'
        else:
            print('wrong webview type!')
            exit(0)
    
        replacestr = f'V5Loader.loadV5(this, V5Loader.CoreType.{typestr}'
        for line in fileinput.input(path, inplace=True):
            line = line.replace(target, replacestr)
            print(line, end='')

    V5_SDK_PATH = os.environ.get('V5_SDK_PATH')

    if V5_SDK_PATH != None:
        # V5_SDK_PATH/v5_cts/src/main/java/com/vivo/v5/webkit/cts/CookieSyncManagerCtsActivity.java
        # V5_SDK_PATH/v5_cts/src/main/java/com/vivo/v5/webkit/cts/WebViewCtsActivity.java
        # V5_SDK_PATH/v5_cts/src/main/java/com/vivo/v5/webkit/cts/WebViewStartupCtsActivity.java
        if V5_SDK_PATH.endswith('/'):
            V5_SDK_PATH = V5_SDK_PATH[0:-1]
        dirname = f'{V5_SDK_PATH}/v5_cts/src/main/java/com/vivo/v5/webkit/cts'
        CookieSyncManagerCtsActivity = f'{dirname}/CookieSyncManagerCtsActivity.java'
        WebViewCtsActivity = f'{dirname}/WebViewCtsActivity.java'
        WebViewStartupCtsActivity = f'{dirname}/WebViewStartupCtsActivity.java'

        replace_webview_inner(CookieSyncManagerCtsActivity, typestr)
        replace_webview_inner(WebViewCtsActivity, typestr)
        replace_webview_inner(WebViewStartupCtsActivity, typestr)
    else:
        print('export V5_SDK_PATH to bashrc!')
        exit(1)


def convertArgs():
    '''
    pycts.py v5
    pycts.py system
    '''
    input_args = sys.argv[1:]
    return input_args

if __name__ == '__main__':
    input_args = convertArgs()

    typestr = WEBVIEW_DROID
    if len(input_args) > 0:
        typestr = input_args[0].upper()
    
    if typestr == WEBVIEW_DROID:
        webview_cts_droid()
    elif typestr == WEBVIEW_V5:
        webview_cts_v5()