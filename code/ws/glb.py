# -*- coding: utf-8 -*-
'''
  ________________________________________
 |                                        |
 | Webscrapping of JNE Website            |
 | Team: Party Switchers                  |
 | Authors: Andrei Batra                  |
 | Date: February, 2020                   |
 |________________________________________|


 =============================================================================
 It just stores nasty looking strings needed for the crawling process.
 =============================================================================
'''

import sys

url = "https://plataformaelectoral.jne.gob.pe/ListaDeCandidatos/Index"

if sys.platform.startswith("darwin"):
    driver_path = ("code/ws/mac/chromedriver")
elif sys.platform.startswith("win32"):
    driver_path = ("code/ws/win32/chromedriver.exe")
else:
    driver_path = ("code/ws/linux/chromedriver")

m_xpaths = {'buscar' :(r"/html[@class='chrome ng-scope']/"
                       "body[@id='sije']/"
                       "main[@class='contenedorGeneal ']/"
                       "div[@class='mainInterno padding-section ng-scope']/"
                       "form[@id='frmBusquedaExpediente']/"
                       "div[@class='buttons__content']/"
                       "button[@class='button button--is-primary bg--is-red']"),
            'view_150': (r"/html[@class='chrome ng-scope']/body[@id='sije']/"
                    "main[@class='contenedorGeneal ']/"
                    "div[@class='mainInterno padding-section ng-scope']/"
                    "form[@id='frmBusquedaExpediente']/"
                    "div[@class='cont-abla-respon nopadding']/"
                    "article[@id='pagad']/"
                    "div[@class='grid__container__footer cleaner']/"
                    "div[@class='grid__button--is-start']/"
                    "div[@class='grid__content__pages']/"
                    "a[@class='pages__number Pages100']"),
            'ver_mas': (r"/html[@class='chrome ng-scope']/body[@id='sije']/"
                    "main[@class='contenedorGeneal ']/"
                    "div[@class='mainInterno padding-section ng-scope']/"
                    "form[@id='frmBusquedaExpediente']/"
                    "div[@class='cont-abla-respon nopadding']/"
                    "table[@class='tablas-estilos alineado-izquierda tabla-limites tabla-notificacion']/"
                    "tbody[@class='tbDesplegable ng-scope'][{}]/"
                    "tr[1]/"
                    "td[@class='ColumT-5']/"
                    "div/div[@class='VotonesVerMas']"),
            'page': (r"/html[@class='chrome ng-scope']/"
                      "body[@id='sije']/main[@class='contenedorGeneal ']/"
                      "div[@class='mainInterno padding-section ng-scope']/"
                      "form[@id='frmBusquedaExpediente']/"
                      "div[@class='cont-abla-respon nopadding']/"
                      "article[@id='pagad']/div[@class='grid__container__footer cleaner']/"
                      "div[@class='grid__button--is-end']/"
                      "div[@class='cleaner grid__content__pages']/"
                      "a[@class='pages__number Page{}']"),
            'row': (r"/html[@class='chrome ng-scope']/"
                    "body[@id='sije']/"
                    "main[@class='contenedorGeneal ']/"
                    "div[@class='mainInterno padding-section ng-scope']/"
                    "form[@id='frmBusquedaExpediente']/"
                    "div[@class='cont-abla-respon nopadding']/"
                    "table[@class='tablas-estilos alineado-izquierda tabla-limites tabla-notificacion']/"
                    "tbody[@class='tbDesplegable ng-scope'][{}]/"
                    "tr[@class='contTabla2da']/"
                    "td[@class='td-conTabla']/"
                    "div[@class='contTabla2da table-detalle']/"
                    "div[@class='cont-abla-respon']/table/tbody/"
                    "tr[@class='ng-scope'][{}]/"
                    "td[@class='ColumT-15 ng-binding'][4]"),
            'hdv': (r"/html[@class='chrome ng-scope']/"
                    "body[@id='sije']/"
                    "main[@class='contenedorGeneal ']/"
                    "div[@class='mainInterno padding-section ng-scope']/"
                    "form[@id='frmBusquedaExpediente']/"
                    "div[@class='cont-abla-respon nopadding']/"
                    "table[@class='tablas-estilos alineado-izquierda tabla-limites tabla-notificacion']/"
                    "tbody[@class='tbDesplegable ng-scope'][{}]/"
                    "tr[@class='contTabla2da']/"
                    "td[@class='td-conTabla']/"
                    "div[@class='contTabla2da table-detalle']/"
                    "div[@class='cont-abla-respon']/"
                    "table/"
                    "tbody/"
                    "tr[@class='ng-scope'][{}]/"
                    "td[@class='ColumT-15 ng-binding'][4]/"
                    "a[@class='boton-redondo']")}


