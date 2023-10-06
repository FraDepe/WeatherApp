from random import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.network.urlrequest import UrlRequest
import pyttsx3


class MyPaintWidget(Widget):

    def on_touch_down(self, touch):
        color = (random(), 1, 1)
        with self.canvas:
            Color(*color, mode='hsv')
            d = 30.
            Ellipse(pos=(touch.x - d / 2, touch.y - d / 2), size=(d, d))
            touch.ud['line'] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, touch.y]


class MyPaintApp(App):

    result = None

    def build(self):
        parent = Widget()
        self.painter = MyPaintWidget()
        clearbtn = Button(text='Clear')
        clearbtn.bind(on_release=self.clear_canvas)
        parent.add_widget(self.painter)
        parent.add_widget(clearbtn)
        request = UrlRequest(f"https://api.openweathermap.org/data/2.5/forecast?lat=41.8933203&lon=12.4829321&appid=c0b583a8bb8b03e64dd0e16bccda95bf&units=metric")
        request.wait()
        self.result = request.result
        return parent

    def clear_canvas(self, obj):
        print(self.result)
        engine = pyttsx3.init()
        frase = "suca"
        engine.say(self.result['list'][0]['weather'][0]['description'])
        engine.runAndWait()


if __name__ == '__main__':
    MyPaintApp().run()