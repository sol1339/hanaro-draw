"""Offline Android lucky draw; no account or network required."""
import csv
import io
import sqlite3
from pathlib import Path
from time import monotonic
from kivy.config import Config
Config.set('graphics', 'width', '1100')
Config.set('graphics', 'height', '650')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from draw_store import DrawStore

FONT = str(Path(__file__).parent / 'assets' / 'NotoSansKR.ttf')
LabelBase.register(name='Korean', fn_regular=FONT)
GREEN = (.06,.18,.15,1)
GOLD = (1,.82,.32,1)
WHITE = (.96,.97,.92,1)


def label(text='', size=18, **kw):
    w=Label(text=text, font_name=FONT, font_size=sp(size), halign='center', valign='middle', **kw)
    w.bind(size=lambda obj,value: setattr(obj,'text_size',value))
    return w


def button(text, callback, color=GOLD, **kw):
    w=Button(text=text, font_name=FONT, font_size=sp(18), background_normal='',
             background_color=color, color=GREEN, **kw)
    w.bind(on_release=callback)
    return w


class HanaroApp(App):
    title='하나로마트 행운 추첨'
    def build(self):
        Window.clearcolor=GREEN
        Window.softinput_mode='below_target'
        self.running=False; self.event=None; self.tick=0; self.modals=0
        self.keys=set(); self.last_action=0; self.pending_csv=None
        Path(self.user_data_dir).mkdir(parents=True,exist_ok=True)
        self.store=DrawStore(Path(self.user_data_dir)/'draw_state.sqlite3')
        root=BoxLayout(orientation='vertical',padding=dp(16),spacing=dp(8))
        root.add_widget(label('하나로마트  |  김장맞이 고객감사',20,size_hint_y=None,height=dp(40)))
        self.stats=label('',13,size_hint_y=None,height=dp(28)); root.add_widget(self.stats)
        self.badge=label('행운을 직접 뽑아보세요!',24,color=GOLD,size_hint_y=.25); root.add_widget(self.badge)
        self.result=label('시작 버튼을 눌러주세요',34,color=WHITE,size_hint_y=.55); root.add_widget(self.result)
        self.hint=label('버튼 터치 또는 Enter 키로 시작 / 멈춤',14,size_hint_y=None,height=dp(38)); root.add_widget(self.hint)
        self.go=button('추첨 시작',lambda *_:self.toggle(),size_hint_y=None,height=dp(70)); root.add_widget(self.go)
        footer=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        self.admin=button('경품 설정',lambda *_:self.settings(),color=(.7,.86,.78,1))
        self.reset_btn=button('초기화',lambda *_:self.confirm_reset(),color=(.7,.86,.78,1))
        self.export_btn=button('기록 저장',lambda *_:self.export(),color=(.7,.86,.78,1))
        for w in (self.admin,self.reset_btn,self.export_btn): footer.add_widget(w)
        root.add_widget(footer)
        Window.bind(on_key_down=self.key_down,on_key_up=self.key_up)
        if platform=='android':
            from android import activity
            activity.bind(on_activity_result=self.activity_result)
        self.refresh()
        history=self.store.history()
        if history:
            i,t,r,n=history[-1]
            self.badge.text='최근 저장 결과'
            self.result.text=f'{r}등 · {n}' if r else '꽝'
            self.hint.text=f'추첨번호 {i:05d} · 다음 고객은 시작을 눌러주세요'
        return root

    def refresh(self):
        rows=self.store.rows(); total=sum(q for _,_,q,u in rows); used=sum(u for _,_,q,u in rows)
        self.stats.text=f'전체 {total:,}회  |  완료 {used:,}회  |  남은 기회 {total-used:,}회'
        self.go.disabled=used>=total
        for w in (self.admin,self.reset_btn,self.export_btn): w.disabled=self.running

    def popup(self,content):
        p=Popup(title='',separator_height=0,content=content,size_hint=(.94,.94),auto_dismiss=False)
        self.modals+=1
        p.bind(on_dismiss=lambda *_:self.modal_closed())
        p.open(); return p

    def modal_closed(self):
        self.modals=max(0,self.modals-1); self.keys.clear()

    def notice(self,text):
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(16))
        box.add_widget(label(text,18))
        close=button('확인',lambda *_:p.dismiss(),size_hint_y=None,height=dp(50))
        box.add_widget(close); p=self.popup(box)

    def key_down(self,window,key,scan,codepoint,modifiers):
        if key in (13,271):
            if key not in self.keys and not self.modals:
                self.keys.add(key); self.toggle()
            return not bool(self.modals)
        if key==27 and not self.modals:
            self.cancel_animation()
            return True
        return False

    def key_up(self,window,key,*args):
        self.keys.discard(key)
        return key in (13,271) and not self.modals

    def toggle(self):
        if self.modals or self.go.disabled or monotonic()-self.last_action<.35: return
        self.last_action=monotonic()
        if self.running:
            self.running=False
            if self.event: self.event.cancel(); self.event=None
            try:
                i,r,n=self.store.draw()
                self.badge.text=f'축하합니다!  {r}등 당첨' if r else '다음 기회에 만나요'
                self.result.text=n if r else '아쉽지만 꽝입니다'
                self.hint.text=f'추첨번호 {i:05d} · 자동 저장 완료'
            except (ValueError,sqlite3.Error) as e:
                self.result.text='추첨을 완료하지 못했습니다'; self.notice(str(e))
            self.go.text='추첨 시작'; self.go.background_color=GOLD
        else:
            self.running=True
            self.go.text='멈춤'; self.go.background_color=(1,.48,.32,1)
            self.badge.text='행운 추첨 중'
            self.hint.text='원하는 순간에 멈춤을 눌러주세요'
            self.animate(0); self.event=Clock.schedule_interval(self.animate,.12)
        self.refresh()

    def animate(self,dt):
        words=['두근두근','행운을 담는 중','오늘의 주인공은?','김장맞이 행운!']
        self.result.text=words[self.tick%4]+'\n'+'● '*(self.tick%3+1); self.tick+=1

    def cancel_animation(self):
        if not self.running: return
        if self.event: self.event.cancel(); self.event=None
        self.running=False; self.go.text='추첨 시작'; self.go.background_color=GOLD
        self.badge.text='추첨 대기'; self.result.text='시작 버튼을 눌러주세요'
        self.hint.text='추첨 취소 · 수량은 차감되지 않았습니다'; self.refresh()

    def settings(self):
        if self.running: return
        rows=self.store.rows()
        box=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(8))
        box.add_widget(label('경품 설정 · 수량은 전체 배정량입니다',20,size_hint_y=None,height=dp(35)))
        scroll=ScrollView(do_scroll_x=False)
        form=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(8))
        form.bind(minimum_height=form.setter('height')); scroll.add_widget(form); box.add_widget(scroll)
        def entry(text,numeric=False):
            return TextInput(text=str(text),multiline=False,font_name=FONT,font_size=sp(17),
                             input_filter='int' if numeric else None,size_hint_y=None,height=dp(46))
        form.add_widget(label('총 추첨 수량 (당첨 + 꽝)',16,size_hint_y=None,height=dp(28)))
        total=entry(sum(q for _,_,q,u in rows),True); form.add_widget(total)
        fields=[]
        for r,n,q,u in rows[1:]:
            form.add_widget(label(f'{r}등  |  추첨 완료 {u:,}개  ·  남은 수량 {q-u:,}개',16,size_hint_y=None,height=dp(32)))
            row=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(8))
            name=entry(n); qty=entry(q,True); qty.size_hint_x=.3
            row.add_widget(name); row.add_widget(qty); form.add_widget(row); fields.append((name,qty))
        preview=label('',15,size_hint_y=None,height=dp(35)); box.add_widget(preview)
        def recalc(*_):
            try: preview.text=f'꽝 자동 배정: {int(total.text)-sum(int(q.text) for n,q in fields):,}개'
            except ValueError: preview.text='수량을 입력하세요'
        total.bind(text=recalc)
        for n,q in fields:q.bind(text=recalc)
        recalc()
        controls=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10))
        def save(*_):
            try:self.store.configure(int(total.text),[(n.text,int(q.text)) for n,q in fields])
            except (ValueError,sqlite3.Error) as e:self.notice(str(e)); return
            self.refresh(); p.dismiss()
        controls.add_widget(button('설정 저장',save)); controls.add_widget(button('취소',lambda *_:p.dismiss()))
        box.add_widget(controls); p=self.popup(box)

    def confirm_reset(self):
        if self.running:return
        box=BoxLayout(orientation='vertical',padding=dp(18),spacing=dp(12))
        box.add_widget(label('추첨을 초기화할까요?\n\n경품명과 배정 수량은 유지됩니다.\n추첨 기록과 차감 수량은 삭제되며,\n추첨번호는 1번부터 다시 시작합니다.\n\n필요한 기록은 먼저 저장해 주세요.',20))
        def reset(*_):
            try:self.store.reset()
            except sqlite3.Error as e:self.notice(str(e)); return
            self.badge.text='초기화 완료'; self.result.text='시작 버튼을 눌러주세요'
            self.hint.text='경품 설정 유지 · 새 추첨 준비 완료'; self.refresh(); p.dismiss()
        box.add_widget(button('초기화 실행',reset,color=(1,.5,.35,1),size_hint_y=None,height=dp(50)))
        box.add_widget(button('취소',lambda *_:p.dismiss(),size_hint_y=None,height=dp(50)))
        p=self.popup(box)

    def export(self):
        buf=io.StringIO(newline=''); w=csv.writer(buf); w.writerow(['추첨번호','일시','등수','경품명'])
        for i,t,r,n in self.store.history():
            if n.startswith(('=','+','-','@')):n="'"+n
            w.writerow([i,t,f'{r}등' if r else '꽝',n])
        text='\ufeff'+buf.getvalue()
        if platform!='android':
            path=Path(self.user_data_dir)/'추첨내역.csv'; path.write_text(text,encoding='utf-8')
            self.notice(f'저장 완료\n{path}');return
        try:
            from jnius import autoclass
            Intent=autoclass('android.content.Intent'); activity=autoclass('org.kivy.android.PythonActivity').mActivity
            intent=Intent(Intent.ACTION_CREATE_DOCUMENT); intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType('text/csv'); intent.putExtra(Intent.EXTRA_TITLE,'추첨내역.csv')
            self.pending_csv=text; activity.startActivityForResult(intent,4201)
        except Exception as e:self.pending_csv=None; self.notice(f'파일 저장 창을 열지 못했습니다.\n{e}')

    def activity_result(self,request,result,data):
        if request!=4201:return
        pending=self.pending_csv; self.pending_csv=None
        if result!=-1 or data is None or pending is None:return
        try:
            from jnius import autoclass
            activity=autoclass('org.kivy.android.PythonActivity').mActivity
            stream=activity.getContentResolver().openOutputStream(data.getData(),'wt')
            writer=autoclass('java.io.OutputStreamWriter')(stream,'UTF-8')
            try:writer.write(pending); writer.flush()
            finally:writer.close()
            message='추첨 내역을 저장했습니다.'
        except Exception as e:message=f'저장 실패: {e}'
        Clock.schedule_once(lambda dt:self.notice(message),0)

    def on_pause(self):
        self.cancel_animation(); self.keys.clear(); return True

    def on_resume(self):
        self.keys.clear()

    def on_stop(self):
        if hasattr(self,'store'):self.store.db.close()

if __name__=='__main__':HanaroApp().run()
