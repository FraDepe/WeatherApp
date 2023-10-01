from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.metrics import dp
from kivymd.uix.tab.tab import MDTabsBase, MDTabs
from kivymd.uix.floatlayout import MDFloatLayout
import datetime
from geopy.geocoders import Nominatim
import json



class MainPage(Screen):
    
    location = ObjectProperty(None)
    request = None
    city = ""

    def search(self):
        self.city = self.location.text
        self.location.text = ""

    def listenToSearch(self):
        pass

class ForecastPage(Screen):

    city = StringProperty()

    def on_enter(self):
        main_page = self.manager.get_screen('main')
        self.city = main_page.city
        gn = Nominatim(user_agent='WeatherApp')
        coordinates = gn.geocode(self.city)
        print(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf")
        req = UrlRequest(f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates.latitude}&lon={coordinates.longitude}&appid=c0b583a8bb8b03e64dd0e16bccda95bf")
        req.wait()
        print(req.result)
        self.request = req
        return req
        

    def getIcon(self):
        main_page = self.manager.get_screen('main')

        return f"https://openweathermap.org/img/wn/{self.request.result['weather'][0]['icon']}@2x.png"

    def getDay(self,day_to_add):
        day = datetime.datetime.now()
        if day_to_add == 0:
            return "Today"
        elif day_to_add == 1:
            return "Tomorrow"
        else: 
            return (day + datetime.timedelta(day_to_add)).strftime('%A')
    

class PageManager(ScreenManager):
    pass



class WeatherApp(MDApp):
    api_key = "c0b583a8bb8b03e64dd0e16bccda95bf"
    def build(self):
        kv = Builder.load_file('weather.kv')
        Window.size = (450,800)
        return kv






class Tab(MDFloatLayout, MDTabsBase):
    pass



if __name__ == '__main__':
    WeatherApp().run()