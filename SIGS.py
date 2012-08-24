import webapp2
import jinja2
import os
import wsgiref
import logging
from google.appengine.api import users, images, conversion
from google.appengine.ext import db
from model.model import *
#from utils import Constantes
import traceback
import datetime
import json as json
import hashlib
#from dateutil.relativedelta import relativedelta
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
#jinja_environment.filters['datetimeformat'] = datetimeformat 
#
#def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
#    return value.strftime(format)


class RenderResponseHandler(webapp2.RequestHandler):
    def __init__(self, request=None, response=None):
        self.nombreUsuario = obtenerUsuarioTablaAdminUser().nombre if obtenerUsuarioTablaAdminUser() else None
        self.initialize(request, response)
        
    def doRender(self, tname='index.html',values = {}):
        temp = os.path.join(os.path.dirname(__file__),
                            'templates/'+tname)
        logging.info('msg'+temp)
        if not os.path.isfile(temp):
            return False
        
        #aca no me conviene utilizar la variable de clase nombreUsuario porque no se actualiza la misma en el constructor por ejemplo
        #cuando hacemos una insercion en Usuario.  
        nombreUsuario = obtenerUsuarioTablaAdminUser() if obtenerUsuarioTablaAdminUser() else None
        sindicatoActual = obtenerSindicatoActual()  
        #se hace una copia del diccionario que se recibe como parametro, 
        #para agregar el indice path y otros valores que se quieran al diccionario
        newval = dict(values)
        #es el path de la pagina sobre la que se hace el request
        newval['path'] = self.request.path
        
        #vamos a agregar al diccionario informacion para manejar el login
        if nombreUsuario:
            url_linktext = 'logout'
        else:
            url_linktext = 'login'
        
        newval['url_linktext'] = url_linktext
        #se muestra el nombre del usuario solo si esta registrado
        newval['nombreUsuario'] = nombreUsuario

        newval['sindicatoActual'] = sindicatoActual
        rsSindicatos = obtenerSindicatosPorAdminUsuario(obtenerUsuarioTablaAdminUser())
        newval['listaSindicatos'] = rsSindicatos
        
        template = jinja_environment.get_template(tname)
        outstr = template.render(newval)
        self.response.out.write(outstr)
        
        return True
    
    def obtenerPagina(self, pOpcion = None, pMensajeInformacion = None):
        try:
            opcion = pOpcion if pOpcion is not None else self.request.get('opcion')
            msgCode = self.request.get('msgCode')
            txt = self.request.get('txt')
            if opcion == 'index':
                if msgCode:
                    self.doRender('index.html',{'notifMsg':getInfoMessageByCode(int(msgCode), txt)})
                else:
                    self.doRender('index.html')
            if opcion == 'autenticar':
                urlLinkText = self.request.get('urlLinkText')
                if urlLinkText == 'login':
                    self.redirect(users.create_login_url('/procesarPagina?opcion=validarRegistro'))
                else:
                    self.redirect(users.create_logout_url('/procesarPagina?opcion=index'))
            elif opcion == 'validarRegistro':
                if not self.nombreUsuario:
                    self.doRender('registro.html',{'mensajeInformacion':'Completando el formulario ya estas suscripto al sistema. '})
                else:
                    self.doRender('index.html')
            elif opcion == 'instrucciones':
                self.doRender('how_to.html')
        except:
            tb = traceback.format_exc()
            #insertarErrorLog(tb)
            self.doRender('error_page.html', {'mensaje':tb})
        
                        
class ProcesarPaginasHandler(RenderResponseHandler):
    def get(self):
        self.obtenerPagina()
        
class RegistroHandler(RenderResponseHandler):
    def post(self):
        try:
            opcion = self.request.get('opcion')
            if opcion == 'registrarUsuario':
                nombre = str(self.request.get('nombre')).decode('utf-8')
                apellido = str(self.request.get('apellido')).decode('utf-8')
                diccioDatosForm = {}
                diccioDatosForm['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre valido" 
                diccioDatosForm['apellido']= "OK" if validateNotEmptyNotNumber(apellido) else "Ingrese un apellido valido"
                isValidDictionary = checkDictionaryForValidation(diccioDatosForm) 
                if isValidDictionary:
                    try:    
                        insertarAdmin(nombre, apellido)
                    except SIGSException as e:
                        diccioDatosForm['errorMessage'] = e.value
                    except Exception as e:
                        diccioDatosForm['errorMessage'] = str(e)
                    else:
                        diccioDatosForm['errorMessage'] = "NONE"
                else:
                    diccioDatosForm['errorMessage'] = "Verifique los datos invalidos ingresados..."
                responseStatus = "OK" if isValidDictionary and diccioDatosForm['errorMessage'] == "NONE" else "ERR"
                diccioDatosForm['responseStatus'] = responseStatus
                jsona = json.dumps(diccioDatosForm)
                self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
                self.response.out.write(jsona)
            if opcion == 'registrarEncargadoSede':
                #Tabla Usuario
                primerNombre = self.request.get('primerNombre')
                segundoNombre = self.request.get('segundoNombre')
                primerApellido = self.request.get('primerApellido')
                segundoApellido = self.request.get('segundoApellido')
                telefono = self.request.get('telefono')
                telefonoReferencia = self.request.get('telefonoReferencia')
                txtDescripcion = str(self.request.get('txtDescripcion'))
                fechaNacimiento = getDatetimeFromString(self.request.get('fechaNacimiento'))
                lugarNacimiento = self.request.get('lugarNacimiento')
                documento = self.request.get('documento')
                sexo = self.request.get('sexo')
                
                #datos Direccion Usuario
                encargadoCalle = self.request.get('encargadoCalle')
                encargadoNumeroCalle = verifyNumber(self.request.get('encargadoNumeroCalle'))
                encargadoProvincia = self.request.get('encargadoProvincia')
                encargadoLocalidad = self.request.get('encargadoLocalidad')
                encargadoCodigoPostal = self.request.get('encargadoCodigoPostal')
                #inserto datos de la direccion en la tabla Direccion y obtengo la entidad
                rsDireccionUsuarioEncargado = insertarDireccion(encargadoCalle, encargadoNumeroCalle, 
                                                                None, encargadoProvincia, encargadoLocalidad, 
                                                                encargadoCodigoPostal, None, None)
                jsonDictionary = []#aca almacenamos las listas de diccionarios diccioDatosForm y listaEncargados para iterar mejor en el popup usuario. 
                diccioDatosForm = {}
                diccioDatosForm['primerNombre'] = "OK" if validateNotEmptyNotNumber(primerNombre) else "Ingrese un primer nombre valido"
                diccioDatosForm['segundoNombre'] = "OK" if not is_number(segundoNombre) else "Ingrese un segundo nombre valido"
                diccioDatosForm['primerApellido'] = "OK" if validateNotEmptyNotNumber(primerApellido) else "Ingrese un apellido valido"
                diccioDatosForm['segundoApellido'] = "OK" if not is_number(segundoApellido) else "Ingrese un apellido materno valido"
                diccioDatosForm['fechaNacimiento'] = "OK" if fechaNacimiento else "Ingrese una fecha de nacimiento valida"
                diccioDatosForm['lugarNacimiento'] = "OK" if lugarNacimiento else "Ingrese un lugar de nacimiento valido"
                diccioDatosForm['documento'] = "OK" if documento else "Ingrese un documento valido"
                diccioDatosForm['encargadoCalle'] = "OK" if encargadoCalle else "Ingrese una calle valida"
                diccioDatosForm['encargadoNumeroCalle'] = "OK" if validateNotEmptyIsNumber(encargadoNumeroCalle) else "Ingrese un numero de calle valido"
                diccioDatosForm['encargadoProvincia'] = "OK" if encargadoProvincia else "Ingrese una provincia valida"
                diccioDatosForm['encargadoLocalidad'] = "OK" if encargadoLocalidad else "Ingrese una localidad valida"
                
                
                diccioDatosForm = validateJsonResponseNoDumps(diccioDatosForm, insertarUsuario,
                                                    primerNombre, segundoNombre, 
                                                    primerApellido, segundoApellido, 
                                                    telefonoReferencia, telefonoReferencia, 
                                                    txtDescripcion, fechaNacimiento, 
                                                    lugarNacimiento, None, 
                                                    documento, sexo, None, 
                                                    None, None, rsDireccionUsuarioEncargado, obtenerSindicatoActual())
                jsonDictionary.append({'diccioDatosForm':diccioDatosForm})
                listaEncargados = []
                rsUsuariosSindicato = obtenerUsuariosPorSindicato()
                for usuario in rsUsuariosSindicato:
                    listaEncargados.append({'nombre':usuario.primerNombre+' '+primerApellido,'keyId':str(usuario.key())})
                jsonDictionary.append({'listaEncargados':listaEncargados})
                jsona = json.dumps(jsonDictionary)
                self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
                self.response.out.write(jsona)
        except:
            tb = traceback.format_exc()
            logging.info(tb)
            #insertarErrorLog(tb)
            self.doRender('error_page.html', {'mensaje':tb})

class SindicatoHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            self.doRender('sindicato_registrar.html')
        elif opcion == 'detalles':
            keyIdSindicato = self.request.get('keyId')
            rsSindicato = db.get(keyIdSindicato)
            self.doRender('sindicato_detalles.html', {'rsSindicato':rsSindicato})
        elif opcion=='gotoSindicato':
            keySindicato = self.request.get('unionKey')
            rsAdminUser = obtenerUsuarioTablaAdminUser()
            rsSindicato = db.get(keySindicato)
            imagen = rsSindicato.imagen
            
            rsSession = obtenerSession(pUserAdmin = rsAdminUser) 
            #si el usuario ya hizo un insert en la tabla Session, actualizar nomas la tabla
            if rsSession:
                rsSession.user = rsAdminUser
                rsSession.sindicato = rsSindicato
                rsSession.imagen = imagen
                rsSession.put()
            #sino insertamos la nueva entidad    
            else:
                insertarSession(rsAdminUser, rsSindicato, imagen)
            self.redirect('sindicato?opcion=captainmorgan')
        else:
            rsSindicatos = obtenerSindicatosPorAdminUsuario(obtenerUsuarioTablaAdminUser())
            if msgCode:
                self.doRender('sindicatos.html',{'notifMsg':getInfoMessageByCode(int(msgCode), txt),
                                                 'listaSindicatos':rsSindicatos})
            else:
                self.doRender('sindicatos.html')
    
    def post(self): 
        opcion = self.request.get('opcion')
        if opcion == 'registrar':
            #datos sindicato
            nombre = str(self.request.get('nombre')).decode('utf-8')
            telefono = str(self.request.get('telefono')).decode('utf-8')
            descripcion = str(self.request.get('txtDescripcion')).decode('utf-8')
            imagen = images.resize(self.request.get("img"), 400,200 ) if self.request.get("img") else None
            responseStatus = 'OK'
            try:
                insertarSindicato(nombre, telefono, descripcion, imagen)
            except Exception as e:
                responseStatus = str(e)
                self.doRender('sindicato_registrar.html', {'responseStatus':responseStatus,
                                                           'nombre':nombre,
                                                           'telefono':telefono,
                                                           'descripcion':descripcion})
            else:
                self.redirect('/sindicato?opcion=index&msgCode=55&txt=%s'%(nombre))
            

class SedeHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion') #esto es para cuando se quiere acceder a la pagina desde el link y no salamente desde el boton
        hdm = self.request.get('hdm')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            #le pasamos la lista de usuarios registrados, afiliados o no, para que figuren en el combo de posibles encargados
            rsUsuarios = obtenerUsuariosPorSindicato()
            self.doRender('sedes_registrar.html', {'rsUsuarios':rsUsuarios})
        elif opcion == 'detalles':
            keyId = self.request.get('keyId')
            rsSede = db.get(keyId)
            self.doRender('sedes_detalles.html', {'rsSede':rsSede})
        elif opcion=='sedeJSON':
            keyId = self.request.get('keyId')
            rsSede = db.get(keyId)
            listaSedes = ['Nombre: '+rsSede.nombre,'Principal?: '+rsSede.principal,'Telefono: '+rsSede.telefono, 
                          'Direccion: '+rsSede.direccion.calle+' '+str(rsSede.direccion.numeroCalle)+' - '+rsSede.direccion.localidad]
            jsona = json.dumps(listaSedes)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        else:
            listaDiccionarioSedesyEncargadosSede = []
            listaSedes = obtenerListaSedesPorSindicato()
            for sede in listaSedes:
                rsEncargado = obtenerEncargadosSede(sede)
                listaDiccionarioSedesyEncargadosSede.append({'sede':sede,'encargado':rsEncargado})
            if msgCode:#ver porque no me llega aca al momento de crear eliminar una sede. Quiero que me retorne los mensajes para mostrar el notification
                self.doRender('sedes.html', {'listaSedes':listaDiccionarioSedesyEncargadosSede, 'mensajeInfo':hdm,
                                             'notifMsg':getInfoMessageByCode(int(msgCode), txt)})
            else:
                nombreSindicato = obtenerSindicatoActual().nombre
                self.doRender('sedes.html', {'listaSedes':listaDiccionarioSedesyEncargadosSede, 
                                             'mensajeInfo':hdm, 'nombreSindicato':nombreSindicato})
    
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        btnConfirmarEdicion = self.request.get('btnConfirmarEdicion')
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax') 
        btnModificar = self.request.get('btnModificar')
        btnEliminar = self.request.get('btnEliminar')
        radioSedes = self.request.get('radioSedes')
        if btnConfirmarRegistro:
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = verifyNumber(self.request.get('numeroCalle'))
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')
            #datos Sede
            nombre = self.request.get('nombre')
            telefono = self.request.get('telefono')
            isPrincipal = self.request.get('chkSedePrincipal') if self.request.get('chkSedePrincipal') is not '' else 'N' #el valor por defecto del check es 'S' en la pagina 
            descripcion = self.request.get('txtDescripcion')
            fechaRegistroStr = str(self.request.get('fechaRegistro'))
            fechaRegistro = getDatetimeFromString(fechaRegistroStr)
            
            #se setea a N las Sedes definidas como Principales si la que se registra es principal
            if isPrincipal == 'S': setSedesNoSedePrincipal()
            
            jsonDictionary = {}
            jsonDictionary['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre valido"
            jsonDictionary['descripcion'] = "OK" if validateNotEmptyNotNumber(descripcion) else "Ingrese una descripcion valida"
            jsonDictionary['calle'] = "OK" if calle else "Ingrese una calle"
            jsonDictionary['numeroCalle'] = "OK" if validateNotEmptyIsNumber(numeroCalle) else "Ingrese un numero de calle valido"
            jsonDictionary['provincia'] = "OK" if provincia else "Ingrese una provincia valida"
            jsonDictionary['localidad'] = "OK" if localidad else "Ingrese una localidad valida"
            jsonDictionary['fechaRegistro'] = "OK" if fechaRegistro else "Ingrese una fecha valida"
            isValidDictionary = checkDictionaryForValidation(jsonDictionary)
            responseStatus = "ERR"
            rsSede = None
            if isValidDictionary:
                try:    
                    rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = numeroCalle, pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
                    #insertar nueva Sede
                    rsSede = insertarSede(nombre, telefono, isPrincipal, descripcion, fechaRegistro, rsDireccion)
                except SIGSException as e:
                    jsonDictionary['errorMessage'] = e.value
                except Exception as e:
                    jsonDictionary['errorMessage'] = str(e)
                else:
                    jsonDictionary['errorMessage'] = "NONE"
                    responseStatus = "OK"
            else:
                jsonDictionary['errorMessage'] = "Verifique los datos invalidos ingresados..."
            jsonDictionary['responseStatus'] = responseStatus

            #obtengo la entidad Usuario seleccionado desde el combo
            usuarioEncargadoSedeKey = self.request.get('selectUsuarioEncargado')
            if usuarioEncargadoSedeKey and rsSede:
                rsUsuarioEncargadoSede = db.get(usuarioEncargadoSedeKey)
    		    #inserto el Usuario y la Sede en EncargadoSede
                insertarEncargadoSede(rsUsuarioEncargadoSede, rsSede)

            jsona = json.dumps(jsonDictionary)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        elif btnConfirmarEdicion:
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = verifyNumber(self.request.get('numeroCalle'))
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')
            #datos Sede
            nombre = self.request.get('nombre')
            telefono = self.request.get('telefono')
            isPrincipal = self.request.get('chkSedePrincipal') if self.request.get('chkSedePrincipal') is not '' else 'N' #el valor por defecto del check es 'S' en la pagina 
            descripcion = self.request.get('txtDescripcion')
            fechaRegistroStr = str(self.request.get('fechaRegistro'))
            fechaRegistro = getDatetimeFromString(fechaRegistroStr)
            
            #se setea a N las Sedes definidas como Principales si la que se registra es principal
            if isPrincipal == 'S': setSedesNoSedePrincipal()
            
            
            
            jsonDictionary = {}
            jsonDictionary['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre valido"
            jsonDictionary['descripcion'] = "OK" if validateNotEmptyNotNumber(descripcion) else "Ingrese una descripcion valida"
            jsonDictionary['calle'] = "OK" if calle else "Ingrese una calle"
            jsonDictionary['numeroCalle'] = "OK" if validateNotEmptyIsNumber(numeroCalle) else "Ingrese un numero de calle valido"
            jsonDictionary['provincia'] = "OK" if provincia else "Ingrese una provincia valida"
            jsonDictionary['localidad'] = "OK" if localidad else "Ingrese una localidad valida"
            jsonDictionary['fechaRegistro'] = "OK" if fechaRegistro else "Ingrese una fecha valida"
            
            #obtenemos las entidades 
            keyIdSede = self.request.get('keyIdSede')
            keyIdEncargado = self.request.get('keyIdEncargado')
            sede = db.get(keyIdSede)
            direccion = sede.direccion
            encargado = db.get(keyIdEncargado) if keyIdEncargado and keyIdEncargado!='undefined' else None
            
            isValidDictionary = checkDictionaryForValidation(jsonDictionary)
            responseStatus = "ERR"
            if isValidDictionary:
                try:    
                    #actualizamos la direccion
                    direccion.calle = calle
                    direccion.numeroCalle = numeroCalle
                    direccion.provincia = provincia
                    direccion.localidad = localidad
                    direccion.codigoPostal = codigoPostal
                    direccion.put()
                    #actualizamos la sede
                    sede.nombre = nombre
                    sede.telefono = telefono
                    sede.principal = isPrincipal
                    sede.descripcion = descripcion
                    sede.fechaRegistro = fechaRegistro
                    sede.direccion = direccion
                    sede.put()
                except SIGSException as e:
                    jsonDictionary['errorMessage'] = e.value
                except Exception as e:
                    jsonDictionary['errorMessage'] = str(e)
                else:
                    jsonDictionary['errorMessage'] = "NONE"
                    responseStatus = "OK"
            else:
                jsonDictionary['errorMessage'] = "Verifique los datos invalidos ingresados..."
            jsonDictionary['responseStatus'] = responseStatus

            #obtengo la entidad Usuario seleccionado desde el combo
            usuarioEncargadoSedeKey = self.request.get('selectUsuarioEncargado')
            if sede:
                if usuarioEncargadoSedeKey:
                    if encargado:
                        rsUsuarioEncargadoSede = db.get(usuarioEncargadoSedeKey)
                        encargado.usuario = rsUsuarioEncargadoSede
                        encargado.sede = sede
                        encargado.put()
                    else:
                        insertarEncargadoSede(db.get(usuarioEncargadoSedeKey), sede)
                else:
                    if encargado:
                        db.delete(encargado)

            jsona = json.dumps(jsonDictionary)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        elif btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = int(self.request.get('numeroCalle'))
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')
            rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = numeroCalle, pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
            #datos Sede
            nombre = self.request.get('nombre')
            telefono = self.request.get('telefono')
            isPrincipal = self.request.get('chkSedePrincipal') 
            descripcion = self.request.get('txtDescripcion')
            fechaRegistroStr = str(self.request.get('fechaRegistro'))
            fechaRegistro = datetime.datetime.strptime(fechaRegistroStr,'%d/%m/%Y')
            
            #se setea a N las Sedes definidas como Principales si la que se registra es principal
            if isPrincipal == 'S': setSedesNoSedePrincipal()
            #insertar nueva Sede
            rsSede = insertarSede(nombre, telefono, isPrincipal, descripcion, fechaRegistro, rsDireccion)
            
            rsSedes = obtenerListaSedesPorSindicato()
            listaSedes = []
            for sede in rsSedes:
                nombreDireccion = sede.nombre + ' - '+sede.direccion.calle + ' ' +str(sede.direccion.numeroCalle)
                listaSedes.append({'nombre':nombreDireccion,'keyId':str(sede.key())})
            jsona = json.dumps(listaSedes)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        else:
            if btnModificar:
                rsSedes = db.get(radioSedes)
                rsUsuarios = obtenerUsuariosPorSindicato()
                rsEncargado = obtenerEncargadosSede(rsSedes)
                dicciResponse = {'rsSedes':rsSedes,'rsUsuarios':rsUsuarios}
                if rsEncargado:
                    dicciResponse['rsEncargado']=rsEncargado
                self.doRender('sedes_editar.html', dicciResponse)
            elif btnEliminar:
                jsonDictionary = {}
                try:
                    #sede a eliminar
                    rsSede = db.get(radioSedes)
                    
                    #vamos a eliminar las referencias a esa sede de la tabla afiliado
                    rsAfiliados = obtenerAfiliadosPorSede(rsSede)
                    if rsAfiliados:
                        for afiliado in rsAfiliados:
                            afiliado.sede = None
                            afiliado.put()
                    #vamos a eliminar las referencias a esta sede de la tabla EncargadoSede
                    rsEncargadoSede = obtenerEncargadosSede(db.get(radioSedes))
                    if rsEncargadoSede:
                        rsEncargadoSede.delete()
                    #eliminamos la sede
                    db.delete(rsSede)
                    
                    jsonDictionary = {'status': 'OK','mensaje':'OK'}
                except Exception as e:
                    jsonDictionary = {'status': 'ERR','mensaje':str(e)}
                jsona = json.dumps(jsonDictionary)
                self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
                self.response.out.write(jsona)

class ServicioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            self.doRender('servicios_registrar.html')
        elif opcion == 'detalle':  
            keyIdServicio = self.request.get('keyId')
            rsServicio = db.get(keyIdServicio)
            listaEntidadLugares = obtenerListaEntidadesYLugaresPorEntidad(rsServicio)
            logging.info(listaEntidadLugares)
            if msgCode:
                self.doRender('servicios_detalles.html', {'rsServicio':rsServicio, 
                                                      'listaEntidadLugares':listaEntidadLugares,
                                                      'notifMsg':getInfoMessageByCode(int(msgCode))})
            else:
                self.doRender('servicios_detalles.html', {'rsServicio':rsServicio, 
                                                      'listaEntidadLugares':listaEntidadLugares})
        else:
            listaServicios = obtenerListaServiciosPorSindicato()
            if msgCode:
                self.doRender('servicios.html',{'notifMsg':getInfoMessageByCode(int(msgCode), txt),
                                                'listaServicios':listaServicios})
            else:
                self.doRender('servicios.html', {'listaServicios':listaServicios})
                        
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        btnConfirmarEdicion = self.request.get('btnConfirmarEdicion')
        btnEliminar = self.request.get('btnEliminar')
        btnModificar = self.request.get('btnModificar')
        radioServicios = self.request.get('radioServicios')
        if btnEliminar is not None and btnEliminar is not '':
            db.delete(db.get(radioServicios))
            self.redirect('/servicio')
        elif btnModificar is not None and btnModificar is not '':
            rsServicio = db.get(radioServicios)
            self.doRender('servicios_editar.html', {'rsServicio':rsServicio})
        elif btnConfirmarRegistro is not None and btnConfirmarRegistro is not '':
            nombre = self.request.get('nombre')
            descripcion = self.request.get('txtDescripcion')
            observaciones = self.request.get('txtObservaciones')
            codigoDescuento = self.request.get('codigoDescuento')
            
            jsonDictionary = {}
            jsonDictionary['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre valido" 
            jsonDictionary['descripcion'] = "OK" if validateNotEmptyNotNumber(descripcion) else "Ingrese una descripcion valida"
            
            jsona = validateJsonResponse(jsonDictionary, insertarServicio,nombre, descripcion, codigoDescuento, observaciones)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
            
        elif btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            nombre = self.request.get('nombre')
            descripcion = self.request.get('descripcion')
            observaciones = self.request.get('observaciones')
            codigoDescuento = self.request.get('codigoDescuento')
            rsServicio = insertarServicio(nombre, descripcion, codigoDescuento, observaciones)
            
            rsServicios = obtenerListaServiciosPorSindicato()
            listaServicios = []
            for servicio in rsServicios:
                listaServicios.append({'nombre':servicio.nombre,'keyId':str(servicio.key())})
            jsona = json.dumps(listaServicios)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        if btnConfirmarEdicion is not None and btnConfirmarEdicion is not '':
            nombre = self.request.get('nombre')
            descripcion = self.request.get('txtDescripcion')
            prestador = self.request.get('prestador')
            #condiciones = self.request.get('condiciones')
            fechaExpiracion = str(self.request.get('fechaExpiracion'))
            prestadoEn = self.request.get('prestadoEn')
            personaReferencia = self.request.get('personaReferencia')
            telefonoPersonaReferencia = self.request.get('telefonoPersonaReferencia')
            updateServicio(db.get(self.request.get('keyServicios')), descripcion, prestador, 
                           datetime.datetime.strptime(fechaExpiracion,'%d/%m/%Y'), 
                           prestadoEn, personaReferencia, telefonoPersonaReferencia)
            self.redirect('/servicio')
        
class EntidadConvenioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            #le pasamos la lista de usuarios registrados, afiliados o no, para que figuren en el combo de posibles encargados
            rsUsuarios = obtenerUsuariosPorSindicato()
            self.doRender('entidadconvenio_registrar.html',{'rsUsuarios':rsUsuarios})
        else:
            rsEntidadConvenio = obtenerEntidadConvenioRelacionadaSindicato()
            if msgCode:
                self.doRender('entidadconvenio.html',{'notifMsg':getInfoMessageByCode(int(msgCode), txt),
                                                      'listaEntidadConvenio':rsEntidadConvenio})
            else:
                self.doRender('entidadconvenio.html',{'listaEntidadConvenio':rsEntidadConvenio})
        
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        if btnConfirmarRegistro is not None and btnConfirmarRegistro is not '':
            nombre = self.request.get('nombre')
            tipoDeEmpresa = self.request.get('txtTipoEmpresa') if self.request.get('txtTipoEmpresa') is not None and self.request.get('txtTipoEmpresa') is not '' else self.request.get('radioTipoEmpresa') 
            telefonoEmpresa = self.request.get('telefono')
            fechaCreacion = getDatetimeFromString(str(self.request.get('fechaCreacion')))
            fechaExpiracion = getDatetimeFromString(str(self.request.get('fechaExpiracion')))
            condicionesConvenio = self.request.get('txtCondicionesConvenio')
            observaciones = self.request.get('txtObservaciones')
            
            #campos de entidad Direccion
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = self.request.get('numeroCalle') 
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')

            jsonDictionary = {}
            jsonDictionary['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre valido"
            jsonDictionary['fechaCreacion'] = "OK" if fechaCreacion else "Ingrese una fecha valida de creacion"
            jsonDictionary['condicionesConvenio'] = "OK" if validateNotEmptyNotNumber(condicionesConvenio) else "Ingrese algunas condiciones validas del convenio"
            #jsonDictionary['tipoDeEmpresa'] = "OK" if tipoDeEmpresa else "Ingrese un tipo de empresa valido"
            jsonDictionary['calle'] = "OK" if calle else "Ingrese una calle"
            jsonDictionary['numeroCalle'] = "OK" if validateNotEmptyIsNumber(numeroCalle) else "Ingrese un numero de calle valido"
            jsonDictionary['provincia'] = "OK" if provincia else "Ingrese una provincia valida"
            jsonDictionary['localidad'] = "OK" if localidad else "Ingrese una localidad valida"
            
            isValidDictionary = checkDictionaryForValidation(jsonDictionary)
            responseStatus = "ERR"
            rsEntidadConvenio = None
            if isValidDictionary:
                rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = int(numeroCalle), pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
                try:    
                    rsEntidadConvenio = insertarEntidadConvenio(
                                    nombre, 
                                    tipoDeEmpresa, 
                                    telefonoEmpresa, 
                                    fechaCreacion, 
                                    fechaExpiracion, 
                                    rsDireccion, 
                                    condicionesConvenio, 
                                    observaciones)         
                    #insertamos ahora en la tabla EntidadConvenioSindicato
                    insertarEntidadConvenioSindicato(rsEntidadConvenio)
                    
                    #insertamos en la tabla PersonaReferenciaEntidadConvenio
                    usuarioEncargadoEntidadConvenioKey = str(self.request.get('selectUsuarioEncargado')) #obtengo la entidad Usuario seleccionado desde el combo
                    if usuarioEncargadoEntidadConvenioKey != 'load':
                        rsUsuarioEncargadoEntidadConvenio = db.get(usuarioEncargadoEntidadConvenioKey)
                        #inserto el Usuario y la Sede en PersonaReferenciaEntidadConvenio
                        insertarPersonaReferenciaEntidadConvenio(rsUsuarioEncargadoEntidadConvenio, rsEntidadConvenio)
                except SIGSException as e:
                    jsonDictionary['errorMessage'] = e.value
                except Exception as e:
                    jsonDictionary['errorMessage'] = str(e)
                else:
                    jsonDictionary['errorMessage'] = "NONE"
                    responseStatus = "OK"
            else:
                jsonDictionary['errorMessage'] = "Verifique los datos invalidos ingresados..."
            jsonDictionary['responseStatus'] = responseStatus
            
            jsona = json.dumps(jsonDictionary)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        if btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            nombre = self.request.get('nombre')
            tipoDeEmpresa = self.request.get('tipoEmpresa') 
            telefonoEmpresa = self.request.get('telefono')
            fechaCreacion = str(self.request.get('fechaCreacion'))
            fechaExpiracion = str(self.request.get('fechaExpiracion'))
            condicionesConvenio = self.request.get('txtCondicionesConvenio')
            observaciones = self.request.get('txtObservaciones')
            
            #campos de entidad Direccion
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = int(self.request.get('numeroCalle'))
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')
            rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = numeroCalle, pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
            
            rsEntidadConvenio = insertarEntidadConvenio(
                                    nombre, 
                                    tipoDeEmpresa, 
                                    telefonoEmpresa, 
                                    datetime.datetime.strptime(fechaCreacion,'%d/%m/%Y'), 
                                    datetime.datetime.strptime(fechaExpiracion,'%d/%m/%Y'), 
                                    rsDireccion, 
                                    condicionesConvenio, 
                                    observaciones)         
            
            #insertamos ahora en la tabla EntidadConvenioSindicato
            insertarEntidadConvenioSindicato(rsEntidadConvenio)
            
            rsEntidadConvenioAll = obtenerEntidadConvenioRelacionadaSindicato()
            diccionarioEntidadConvenio = []
            for entidad in rsEntidadConvenioAll:
                diccionarioEntidadConvenio.append({'keyId':str(entidad.key()),'nombre':entidad.nombre}) 
            
            jsona = json.dumps(diccionarioEntidadConvenio)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
                
            
class LugarPrestacionServicioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            rsSedes = obtenerListaSedesPorSindicato()
            self.doRender('lugarprestacionservicio_registrar.html', {'listaSedes':rsSedes})
        elif opcion == 'popup_registrar':
            rsSedes = obtenerListaSedesPorSindicato()
            self.doRender('popup_lugarprestacionservicio.html', {'listaSedes':rsSedes})
        else:
            rsLugarPrestacionServicio = obtenerLugarPrestacionServicioRelacionadoSindicato()
            if msgCode:
                self.doRender('lugarprestacionservicio.html', {'listaLugarPrestacionServicio':rsLugarPrestacionServicio,
                                                               'notifMsg':getInfoMessageByCode(int(msgCode), txt)})
            else:
                self.doRender('lugarprestacionservicio.html', {'listaLugarPrestacionServicio':rsLugarPrestacionServicio})
            
    
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        if btnConfirmarRegistro is not None and btnConfirmarRegistro is not '':
            nombre = self.request.get('nombre')
            telefono = self.request.get('telefono')
            observacion = self.request.get('txtObservaciones')

            radioDireccion = self.request.get('radioDireccion')
            diccioDatosForm = {}
            diccioDatosForm['nombre'] = "OK" if validateNotEmptyNotNumber(nombre) else "Ingrese un nombre adecuado"
            responseStatus = "ERR"
            calle = None
            numeroCalle = None
            provincia = None
            localidad = None
            codigoPostal = None
            rsDireccion = None
            #si es S el radioDireccion, es porque la direccion corresponde a la de una Sede
            if radioDireccion == 'S':
                #si no selecciono una sede valida del combo
                try:
                    keyIdSede = str(self.request.get('selectDireccionSede'))#TODO validacion para esto
                    rsSede = db.get(keyIdSede)
                    rsDireccion = rsSede.direccion
                except:
                    diccioDatosForm['errorMessage'] = "Seleccione una sede si en la misma se prestaran servicios"
                    diccioDatosForm['responseStatus'] = responseStatus
                    jsona = json.dumps(diccioDatosForm)
                    self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
                    self.response.out.write(jsona)
                    return
            elif radioDireccion == 'N':
                try:
                    #controlamos que se ingresen bien los datos de la direccion
                    calle = self.request.get('calle')
                    numeroCalle = self.request.get('numeroCalle') 
                    provincia = self.request.get('provincia')
                    localidad = self.request.get('localidad')
                    codigoPostal = self.request.get('codigoPostal')
                    
                    diccioDatosForm['calle'] = "OK" if calle else "Ingrese una calle"
                    diccioDatosForm['numeroCalle'] = "OK" if validateNotEmptyIsNumber(numeroCalle) else "Ingrese un numero de calle valido"
                    diccioDatosForm['provincia'] = "OK" if provincia else "Ingrese una provincia valida"
                    diccioDatosForm['localidad'] = "OK" if localidad else "Ingrese una localidad valida"
                    
                    rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = int(numeroCalle), pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
                except Exception as e:
                    diccioDatosForm['errorMessage'] = "Verifique los datos de la direccion"
                    diccioDatosForm['responseStatus'] = responseStatus
                    jsona = json.dumps(diccioDatosForm)
                    self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
                    self.response.out.write(jsona)
                    return
            
            isValidDictionary = checkDictionaryForValidation(diccioDatosForm)
            if isValidDictionary:
                try:
                    rsLugarPrestacionServicio = insertarLugarPrestacionServicio(nombre, telefono, observacion, rsDireccion)
        
                    #insertamos en la tabla relacional LugarPrestacionServicioSindicato 
                    insertarLugarPrestacionServicioSindicato(rsLugarPrestacionServicio)
                    
                except SIGSException as e:
                    diccioDatosForm['errorMessage'] = e.value
                except Exception as e:
                    diccioDatosForm['errorMessage'] = str(e)
                else:
                    diccioDatosForm['errorMessage'] = "NONE"
                    responseStatus = "OK"
            else:
                diccioDatosForm['errorMessage'] = "Debe especificar la direccion de Lugar de Prestacion del servicio"
            diccioDatosForm['responseStatus'] = responseStatus
            jsona = json.dumps(diccioDatosForm)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        elif btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            nombre = self.request.get('nombre')
            telefono = self.request.get('telefono')
            observacion = self.request.get('txtObservaciones')
            
            #vamos a obtener la direccion
            radioDireccion = self.request.get('radioDireccion')
            #si es S el radioDireccion, es porque la direccion corresponde a la de una Sede
            if radioDireccion == 'S':
                keyIdSede = self.request.get('selectDireccionSede')
                rsSede = db.get(keyIdSede)
                rsDireccion = rsSede.direccion
            elif radioDireccion == 'N':
                calle = self.request.get('calle')
                numeroCalle = int(self.request.get('numeroCalle'))
                provincia = self.request.get('provincia')
                localidad = self.request.get('localidad')
                codigoPostal = self.request.get('codigoPostal')
                rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = numeroCalle, pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
            
            rsLugarPrestacionServicio = insertarLugarPrestacionServicio(nombre, telefono, observacion, rsDireccion)
            
            #insertamos en la tabla relacional LugarPrestacionServicioSindicato 
            insertarLugarPrestacionServicioSindicato(rsLugarPrestacionServicio)
            #vamos a completar el select
            rsLugarPrestacionServicio = obtenerLugarPrestacionServicioRelacionadoSindicato()
            listaLugarPrestacionServicio = []
            for lugarPrestacion in rsLugarPrestacionServicio:
                listaLugarPrestacionServicio.append({'keyId':str(lugarPrestacion.key()),'nombreCalle':lugarPrestacion.direccion.calle,
                                                     'numeroCalle':lugarPrestacion.direccion.numeroCalle,'nombre':lugarPrestacion.nombre})
            
            jsona = json.dumps(listaLugarPrestacionServicio)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
            
        
        
            
class ServicioEntidadConvenioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        if opcion == 'registrar':
            rsServicio = db.get(str(self.request.get('servicioKeyId')))
            rsEntidadesConvenio = obtenerEntidadConvenioRelacionadaSindicato() 
            rsLugaresPrestacionServicios = obtenerLugarPrestacionServicioRelacionadoSindicato()
            self.doRender('servicioentidadconvenio_registrar.html',{'rsServicio':rsServicio,
                                                                    'listaEntidadesConvenio':rsEntidadesConvenio,
                                                                    'listaLugaresPrestacionServicos':rsLugaresPrestacionServicios})
        else:
            self.redirect('/servicios')
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        if btnConfirmarRegistro:
            jsonDictionary = {}
            rsServicio = db.get(self.request.get('servicioKeyId'))
            try:
                rsEntidadConvenio = db.get(self.request.get('selectEntidadesConvenio'))
                jsonDictionary['entidadConvenio'] = "OK"
            except:
                jsonDictionary['entidadConvenio'] = "Debe seleccionar una entidad convenio"
            try:
                rsLugarPrestacionServicio = db.get(self.request.get('selectLugarPrestacionServicio'))
                jsonDictionary['lugarPrestacion'] = "OK"
            except:
                jsonDictionary['lugarPrestacion'] = "Debe seleccionar un lugar de prestacion del servicio"
            
            if checkDictionaryForValidation(jsonDictionary):
                try:
                    insertarServicioEntidadConvenio(rsServicio, rsEntidadConvenio, rsLugarPrestacionServicio)
                    jsonDictionary['responseStatus'] = 'OK'
                except Exception as e:
                    jsonDictionary['errorMessage'] = str(e)
                    jsonDictionary['responseStatus'] = 'ERR'
            else:
                jsonDictionary['responseStatus'] = 'ERR'
                jsonDictionary['errorMessage'] = 'Verifique los datos erroneos'
            jsona = json.dumps(jsonDictionary)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
            
class AfiliadoHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        msgCode = self.request.get('msgCode')
        txt = self.request.get('txt')
        if opcion == 'registrar':
            rsSedes = obtenerListaSedesPorSindicato()
            rsEntidadesLaborales = obtenerEntidadesLaborales()
            rsAfiliadosTitulares = obtenerAfiliados('TITULAR')
            self.doRender('afiliado_registrar.html', {'listaSedes':rsSedes,'listaEntidadLaboral':rsEntidadesLaborales,
                                                      'listaAfiliadosTitulares':rsAfiliadosTitulares})
        elif opcion == 'detalles':
            keyId = self.request.get('keyId')
            rsAfiliado = db.get(keyId)
            rsDatosLaborales = obtenerDatosLaborales(None, rsAfiliado)
            rsAfiliadoServicio = obtenerAfiliadoServicio(rsAfiliado)
            for dato in rsDatosLaborales:
                logging.info(dato.entidadLaboral.nombre)
            self.doRender('afiliado_detalles.html', {'rsAfiliado':rsAfiliado,'rsDatosLaborales':rsDatosLaborales,
                                                     'rsAfiliadoServicio':rsAfiliadoServicio})
        elif opcion == 'afiliadoJSON':
            keyId = self.request.get('keyId')
            rsAfiliado = db.get(keyId)
            jsonResponse = {
                            'nombre':rsAfiliado.usuario.primerNombre,
                            'carnet':rsAfiliado.carnet,
                            'parentesco':rsAfiliado.parentesco,
                            'deuda':rsAfiliado.deuda
                            }
            jsona = json.dumps(jsonResponse)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona) 

        else:
            rsAfiliados = obtenerAfiliados()
            if msgCode:
                self.doRender('afiliados.html', {'listaAfiliados':rsAfiliados,
                                                 'notifMsg':getInfoMessageByCode(int(msgCode), txt)})
            else:
                self.doRender('afiliados.html', {'listaAfiliados':rsAfiliados})
            
    def post(self):
        btnConfirmarRegistro = self.request.get('btnConfirmarRegistro')
        if btnConfirmarRegistro is not None and btnConfirmarRegistro is not '':
            jsonDictionary = {}
            #Tabla Usuario
            primerNombre = self.request.get('primerNombre')
            segundoNombre = self.request.get('segundoNombre')
            primerApellido = self.request.get('primerApellido')
            segundoApellido = self.request.get('segundoApellido')
            telefono = self.request.get('telefono')
            telefonoReferencia = self.request.get('telefonoReferencia')
            txtDescripcion = str(self.request.get('txtDescripcionafiliado'))
            fechaNacimiento = getDatetimeFromString(str(self.request.get('fechaNacimiento')))
            lugarNacimiento = self.request.get('lugarNacimiento')
            documento = self.request.get('documento')
            sexo = self.request.get('sexo')
            
            #datos Direccion Usuario
            afiliadoCalle = self.request.get('afiliadoCalle')
            afiliadoNumeroCalle = self.request.get('afiliadoNumeroCalle')
            afiliadoProvincia = self.request.get('afiliadoProvincia')
            afiliadoLocalidad = self.request.get('afiliadoLocalidad')
            afiliadoCodigoPostal = self.request.get('afiliadoCodigoPostal')
            
            #datos afiliacion
            carnet = self.request.get('carnet')
            fechaRegistro = getDatetimeFromString(str(self.request.get('fechaRegistro')))
            categoriaProfesional = self.request.get('categoriaProfesional')
            lugarEstudio = self.request.get('lugarEstudio')
            radioEstadoCivil = self.request.get('radioEstadoCivil')
            antiguedadLaboral = self.request.get('antiguedadLaboral')
            numeroSuscripcion = verifyNumber(self.request.get('numeroSuscripcion'))
            categoriaSuscripcion = self.request.get('categoriaSuscripcion')
            sede = self.request.get('selectDireccionSede')
            
            
            #comenzamos a llenar el diccionario JSON
            jsonDictionary['fechaRegistro'] = "OK" if fechaRegistro else "Ingrese una fecha de registro valida"
            jsonDictionary['antiguedadLaboral'] = "OK" if validateNotEmptyIsNumber(antiguedadLaboral) else "Ingrese la antiguedad laboral"
            jsonDictionary['categoriaSuscripcion'] = "OK" if validateNotEmptyNotNumber(categoriaSuscripcion) else "Ingrese la categoria de suscripcion"
            
            jsonDictionary['calle'] = "OK" if afiliadoCalle else "Ingrese una calle"
            jsonDictionary['numeroCalle'] = "OK" if validateNotEmptyIsNumber(afiliadoNumeroCalle) else "Ingrese un numero de calle valido"
            jsonDictionary['provincia'] = "OK" if afiliadoProvincia else "Ingrese una provincia valida"
            jsonDictionary['localidad'] = "OK" if afiliadoLocalidad else "Ingrese una localidad valida"
            
            jsonDictionary['primerNombre'] = "OK" if validateNotEmptyNotNumber(primerNombre) else "Ingrese un primer nombre valido"
            jsonDictionary['primerApellido'] = "OK" if validateNotEmptyNotNumber(primerApellido) else "Ingrese un primer apellido valido"
            jsonDictionary['telefonoPrincipal'] = "OK" if telefono else "Ingrese un telefono valido"
            jsonDictionary['descripcion'] = "OK" if validateNotEmptyNotNumber(txtDescripcion) else "Ingrese una descripcion valida"
            jsonDictionary['fechaNacimiento'] = "OK" if fechaNacimiento else "Ingrese una fecha de nacimiento valida"
            jsonDictionary['lugarNacimiento'] = "OK" if validateNotEmptyNotNumber(lugarNacimiento) else "Ingrese un lugar de nacimiento valido"
            jsonDictionary['documento'] = "OK" if documento else "Ingrese una clave de documento valida"
            jsonDictionary['sexo'] = "OK" if validateNotEmptyNotNumber(sexo) else "Ingrese el sexo del afiliado"
            jsonDictionary['estadoCivil'] = "OK" if validateNotEmptyNotNumber(radioEstadoCivil) else "Ingrese el estado civil"
            #datos sede
            try:
                rsSede = db.get(sede)
                jsonDictionary['sede'] = "OK" 
            except:
                jsonDictionary['sede'] = "Ingrese una sede"
            
            #parentesco
            parentesco = self.request.get('radioParentesco')
            if parentesco:
                jsonDictionary['parentesco'] = "OK"
                if parentesco == 'CARGA_FAMILIAR':
                    selectAfiliadoTitular = self.request.get('selectAfiliadoTitular')
                    try:
                        rsAfiliadoTitular = db.get(selectAfiliadoTitular)
                        jsonDictionary['cargaFamiliar'] = "OK"
                    except:
                        jsonDictionary['cargaFamiliar'] = "Ingrese una carga familiar"
                        
                    parentescoAfiliado = self.request.get('parentescoAfiliado')
                    jsonDictionary['parentescoAfiliadoTitular'] = "OK" if validateNotEmptyNotNumber(parentescoAfiliado) else "Ingrese un parentesco con el afiliado titular"
                elif parentesco == 'TITULAR':
                    #se obtiene la entidad laboral
                    try:
                        entidadLaboral = self.request.get('selectEntidadLaboral')
                        rsEntidadLaboral = db.get(entidadLaboral)
                        jsonDictionary['entidadLaboral'] ="OK"
                    except:
                        jsonDictionary['entidadLaboral'] ="Ingrese la entidad laboral"
                    ocupacion = self.request.get('radioOcupacion')
                    jsonDictionary['ocupacion'] = "OK" if validateNotEmptyNotNumber(ocupacion) else "Ingrese una ocupacion"
                    try:
                        fechaDeIngreso = datetime.datetime.strptime(self.request.get('fechaDeIngreso'),'%d/%m/%Y')
                        jsonDictionary['fechaDeIngreso'] = "OK" 
                    except:
                        jsonDictionary['fechaDeIngreso'] = "Indique una fecha de ingreso"
                    
                    cargo = self.request.get('cargo')
                    departamento= self.request.get('departamento')
                    sueldoBase = self.request.get('sueldoBase')
                    tipoContrato = self.request.get('radioTipoContrato')
                    contacto = self.request.get('contacto')
                    jsonDictionary['cargo'] = "OK" if validateNotEmptyNotNumber(cargo) else "Ingrese el cargo"
                    jsonDictionary['sueldoBase'] = "OK" if validateNotEmptyIsNumber(sueldoBase) else "Ingrese el sueldo base"
            else:
                jsonDictionary['parentesco'] = "Ingrese un parentesco valido"
            #vamos a hacer los insert:
            if checkDictionaryForValidation(jsonDictionary):
                try:
                    rsDireccionUsuario = insertarDireccion(afiliadoCalle, int(afiliadoNumeroCalle), 
                                                                    None, afiliadoProvincia, afiliadoLocalidad, 
                                                                    afiliadoCodigoPostal, None, None)
                 
                    #inserto la entidad Direccion en Usuario y obtengo la entidad Usuario
                    rsUsuario = insertarUsuario(primerNombre, segundoNombre, 
                                    primerApellido, segundoApellido, 
                                    telefono, telefonoReferencia, 
                                    txtDescripcion, fechaNacimiento, 
                                    lugarNacimiento, None, 
                                    documento, sexo, None, 
                                    None, None, rsDireccionUsuario, obtenerSindicatoActual())
                    
                    #insertamos el afiliado
                    rsAfiliado = insertarAfiliado(rsUsuario, carnet, fechaRegistro, categoriaProfesional, lugarEstudio, radioEstadoCivil, parentesco, 
                                     int(antiguedadLaboral), numeroSuscripcion, categoriaSuscripcion, rsSede, float(0), float(0))
                    
                    if parentesco == 'CARGA_FAMILIAR':
                        insertarCargaFamiliar(rsUsuario, rsAfiliadoTitular, parentescoAfiliado)
                
                    elif parentesco == 'TITULAR':
                        insertarDatosLaborales(rsEntidadLaboral, rsAfiliado, ocupacion, fechaDeIngreso, 
                                               cargo, departamento, int(sueldoBase), tipoContrato, contacto)
                    #todo fue bien
                    jsonDictionary['errorMessage'] = "Lo tenemos lo tenemos"
                    jsonDictionary['responseStatus'] = 'OK'
                except Exception as e:
                    jsonDictionary['errorMessage'] = str(e)
                    jsonDictionary['responseStatus'] = 'ERR'
                
            else:
                jsonDictionary['errorMessage'] = "Verifique los campos faltantes"
                jsonDictionary['responseStatus'] = 'ERR'
            
            jsona = json.dumps(jsonDictionary)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)  
  
class ServicioAfiliadoHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        if opcion == 'registrar':
            keyIdAfiliado = str(self.request.get('keyIdAfiliado'))
            rsAfiliado = db.get(keyIdAfiliado)
            rsServicios = obtenerListaServiciosPorSindicato()
            rsServiciosAfiliado = obtenerAfiliadoServicio(rsAfiliado)
            #vamos a obtener la lista de los servicios a los que el afiliado aun no fue suscripto
            listaServiciosNoCubiertos = [] 
            listaServiciosAfiliado = []
            for ser in rsServiciosAfiliado:
                listaServiciosAfiliado.append(str(ser.servicio.key()))
            diccioResponse = {'rsAfiliado':rsAfiliado}
            for servicio in rsServicios:
                if str(servicio.key()) not in listaServiciosAfiliado:
                    listaServiciosNoCubiertos.append(servicio)
            if len(listaServiciosNoCubiertos) == 0 and len(rsServiciosAfiliado) > 0:
                pass#no se muestra nada
            elif len(listaServiciosNoCubiertos) == 0 and len(rsServiciosAfiliado) == 0:
                diccioResponse['rsServicio']=rsServicios
            else:
                diccioResponse['rsServicio']=listaServiciosNoCubiertos
            
            self.doRender('popup_afiliado_servicio.html', diccioResponse )
    
    def post(self):
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        if btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            rsAfiliado = db.get(self.request.get('afiliadoHidden'))  
            rsServicio = db.get(self.request.get('selectServicio')) 
            observacion = self.request.get('txtObservaciones') 
            estado = self.request.get('radioEstado')
            #TODO hacer algo para que se incorpore en la respuesta JSON el mensaje de excepcion en caso
            #de que se intente almacenar una relacion existente de afiliado y servicio...
            insertarAfiliadoServicio(rsAfiliado, rsServicio, observacion, estado)
            
            rsServicios = obtenerAfiliadoServicio(rsAfiliado)
            listaServiciosNoVinculadosAlAfiliado = []
            for servicio in rsServicios:
                listaServiciosNoVinculadosAlAfiliado.append({'keyId':str(servicio.servicio.key()),'estado':servicio.estado,
                                      'nombre':servicio.servicio.nombre,'observacion':servicio.observacion})
            jsona = json.dumps(listaServiciosNoVinculadosAlAfiliado)
            self.response.headers.add_header('content-type','application/json',charset='utf-8')
            self.response.out.write(jsona)
            
class EntidadLaboralHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        if opcion == 'entidadLaboralJSON':
            keyId = self.request.get('keyId')
            rsEntidadLaboral = db.get(keyId)
            listaEntidadLaboral = ['Nombre: '+rsEntidadLaboral.nombre,'Tipo: '+rsEntidadLaboral.tipoDeEmpresa,
                                   'Telefono: '+rsEntidadLaboral.telefonoEmpresa,'CUIT: '+rsEntidadLaboral.cuitEmpleador,
                                   'Direccion: '+rsEntidadLaboral.direccion.calle+' '+
                                   str(rsEntidadLaboral.direccion.numeroCalle)+' - '+rsEntidadLaboral.direccion.localidad,
                                   'Numero de Seguridad Social: '+str(rsEntidadLaboral.numeroSeguridadSocial)]
            jsona = json.dumps(listaEntidadLaboral)
            self.response.headers.add_header('content-type','application/json',charset='utf-8')
            self.response.out.write(jsona)
            
    def post(self):
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        if btnConfirmarRegistroAjax is not None and btnConfirmarRegistroAjax is not '':
            nombre = self.request.get('nombre')
            tipoDeEmpresa = self.request.get('tipoDeEmpresa')
            telefonoEmpresa = self.request.get('telefonoEmpresa')
            cuitEmpleador = self.request.get('cuitEmpleador')
            numeroSeguridadSocial = self.request.get('numeroSeguridadSocial')
            
            #datos direccion
            #datos Direccion
            calle = self.request.get('calle')
            numeroCalle = int(self.request.get('numeroCalle'))
            provincia = self.request.get('provincia')
            localidad = self.request.get('localidad')
            codigoPostal = self.request.get('codigoPostal')
            rsDireccion = insertarDireccion(pCalle = calle, pNumeroCalle = numeroCalle, pProvincia = provincia, pLocalidad = localidad, pCodigoPostal = codigoPostal)
            
            insertarEntidadLaboral(nombre, tipoDeEmpresa, telefonoEmpresa, cuitEmpleador, rsDireccion, numeroSeguridadSocial)
            
            rsEntidadesLaborales = obtenerEntidadesLaborales()
            listaEntidadesLaborales = []
            for entidad in rsEntidadesLaborales:
                listaEntidadesLaborales.append({'nombre':entidad.nombre,'keyId':str(entidad.key())})
            jsona = json.dumps(listaEntidadesLaborales)
            self.response.headers.add_header('content-type','application/json',charset='utf-8')
            self.response.out.write(jsona)
            
class ValeServicioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        if opcion == 'registrar':
            keyIdAfiliado = str(self.request.get('keyIdAfiliado'))
            rsAfiliado = db.get(keyIdAfiliado)
            rsServiciosAfiliado = obtenerAfiliadoServicio(rsAfiliado)
            dicci = {'rsAfiliado':rsAfiliado}
            if len(rsServiciosAfiliado) > 0:
                dicci['rsServicio'] = rsServiciosAfiliado
            self.doRender('popup_valeservicio_registrar.html', dicci )
        elif opcion == 'entidadesConvenioPorServicio':
            rsServicio = db.get(self.request.get('servicioKeyId'))
            listaEntidadLugares = obtenerListaEntidadesYLugaresPorEntidad(rsServicio)
            #vamos a serializar los modelos para pasarlos a la salida JSON
            listEntidadLugar = []
            listLugar = []
            for entidadLugar in listaEntidadLugares:
                dict = {'entidadNombre' : str(entidadLugar['entidadConvenio'].nombre)}
                for lugar in entidadLugar['lugaresPrestacionServicio']:
                    listLugar.append({'lugarKey':str(lugar.key()),'nombreLugar':lugar.nombre +' - '+lugar.direccion.calle+' '+str(lugar.direccion.numeroCalle)})
                dict['lugarPrestacion'] = listLugar
                listEntidadLugar.append(dict)
                listLugar=[]#limpiamos la lista de lugares
            jsona = json.dumps(listEntidadLugar)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        elif opcion == 'checkResetMontoSueldoAfiliado':
            keyIdAfiliado = str(self.request.get('keyIdAfiliado'))
            rsAfiliado = db.get(keyIdAfiliado)
            dictJson = {}
            if rsAfiliado.isMontoSueldoNetoActualizado == False:
                dictJson = {'showEnterSaldoDialog':'S'}
            else:
                dictJson = {'showEnterSaldoDialog':'N'}
            jsona = json.dumps(dictJson)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
        elif opcion == 'actualizarMontoNetoSueldo':
            keyIdAfiliado = str(self.request.get('keyIdAfiliado'))
            montoNeto = float(self.request.get('montoNeto'))
            reciboSueldoNro = int(self.request.get('reciboSueldoNro'))
            #se actualiza isMontoSueldoNetoActualizado del Afiliado
            rsAfiliado = db.get(keyIdAfiliado)
            rsAfiliado.isMontoSueldoNetoActualizado = True
            rsAfiliado.montoSueldoNeto = montoNeto
            rsAfiliado.reciboSueldoNroMesActual = reciboSueldoNro
            actualizarAfiliado(rsAfiliado)
            
            dictJson = {'montoNetoSueldo':montoNeto,'reciboSueldoNro':reciboSueldoNro}
            jsona = json.dumps(dictJson)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
            
    def post(self):
        opcion = self.request.get('opcion')
        btnConfirmarRegistroAjax = self.request.get('btnConfirmarRegistroAjax')
        if btnConfirmarRegistroAjax:
            chkLugarVale = self.request.get_all('chkLugarVale') 
            afiliadoHidden = self.request.get('afiliadoHidden') 
            selectServicio = self.request.get('selectServicio')
            txtObservaciones = self.request.get('txtObservaciones')
            monto = float(self.request.get('monto'))
            numeroCuotas = int(self.request.get('salame'))
            fechaPrestacion = datetime.datetime.strptime(str(self.request.get('fechaPrestacion')),'%d/%m/%Y')
            numeroAutorizacion = int(self.request.get('numeroAutorizacion'))
            reciboSueldoNro = self.request.get('reciboSueldoNro')
            
            #obtenemos el afiliado para actualizar el monto de su deuda
            rsAfiliado = db.get(afiliadoHidden) 
            rsAfiliado.deuda = (rsAfiliado.deuda) + monto
            
            
            rsValeServicio = insertarValeServicio(monto, numeroCuotas, chkLugarVale, 
                                 fechaPrestacion, txtObservaciones, int(numeroAutorizacion), 
                                 db.get(selectServicio),int(reciboSueldoNro), 0)
            
            #obtener el montonetosueldo para la insercion de abajo
            rsAccesoServicio = insertarAccesoServicio(actualizarAfiliado(rsAfiliado), rsValeServicio, int(0))
            
            dictJson = {'responseStatus':'OK'}
            jsona = json.dumps(dictJson)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)
            
class AccesoServicioHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        listaMeses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        if opcion == 'detalles':
            accesoServicio = self.request.get('keyId')
            rsAccesoServicio = db.get(accesoServicio)
            montoPagarPorCuota = rsAccesoServicio.vale.monto / rsAccesoServicio.vale.numeroCuotas
            self.doRender('accesoservicio_detalles.html', {'rsAccesoServicio':rsAccesoServicio,
                                                           'montoPagarPorCuota':montoPagarPorCuota})
        elif opcion=='historial':
            lista = []
            anhoBase = 2010
            anhoActual = datetime.datetime.now().year
            mesActual = datetime.datetime.now().month
            
            listaMesesAnhoActual = []
            count = 0
            for mes in listaMeses:
                count +=1
                if count <= mesActual:
                    listaMesesAnhoActual.append(mes)
            
            for element in range(anhoBase, anhoActual+1):
                lista.append(element)
            self.doRender('historial_vales.html', {'listaAnhos':lista,'anhoActual':anhoActual,
                                                   'mesActual':mesActual,'listaMeses':listaMeses,
                                                   'listaMesesAnhoActual':listaMesesAnhoActual})
        elif opcion=='imprimirHistorial':
            anho = int(self.request.get('anho'))
            mes = listaMeses.index(self.request.get('mes'))+1#obtenemos la posicion en la lista del mes  
            rsAccesoServicio = obtenerAccesoServicioMesParametro(anho, mes)
            totalPagosMesActual = 0
            for pago in rsAccesoServicio:
                totalPagosMesActual += float(pago.montoAbonado) 
            self.doRender('historial_vales_detalle.html', { 'rsAccesoServicio':rsAccesoServicio,
                                                           'totalPagosMesActual':totalPagosMesActual,'anho':anho,
                                                           'mesString':self.request.get('mes'),'mes':mes })
        elif opcion=='historialToHtml':
            anho = int(self.request.get('anho'))
            mes = listaMeses.index(self.request.get('mes'))+1#obtenemos la posicion en la lista del mes  
            rsAccesoServicio = obtenerAccesoServicioMesParametro(anho, mes)
            stringTitulo = self.request.get('mes')+'/'+str(anho)
            totalPagosMesActual = 0
            for pago in rsAccesoServicio:
                totalPagosMesActual += float(pago.montoAbonado) 
            self.doRender('historial_vale_html.html', { 'rsAccesoServicio':rsAccesoServicio,'stringTitulo':stringTitulo,'totalPagosMesActual':totalPagosMesActual })

        else:
            rsAccesoServicioVigentes = obtenerAccesoServicioVigentesMesesAnteriores()
            rsAccesoServicioContraidoMesActual = obtenerAccesoServicioContraidoMesActual()
            rsobtenerAccesoServicioPagosMesActual = obtenerAccesoServicioPagosMesActual()
            totalPagosMesActual = 0
            for pago in rsobtenerAccesoServicioPagosMesActual:
                totalPagosMesActual += float(pago.montoAbonado) 
            self.doRender('contabilidad.html', {'rsAccesoServicioVigentes':rsAccesoServicioVigentes, 
                                                'rsAccesoServicioContraidoMesActual':rsAccesoServicioContraidoMesActual,
                                                'rsobtenerAccesoServicioPagosMesActual':rsobtenerAccesoServicioPagosMesActual,
                                                'totalPagosMesActual':totalPagosMesActual})
            
            
    def post(self):
        opcion = self.request.get('opcion')
        btnRegistrarAccesoServicio = self.request.get('btnRegistrarAccesoServicio')
        if btnRegistrarAccesoServicio:
            numeroCuotasPagadas = int(self.request.get('cuotaPagada'))
            montoAbonado = float(self.request.get('montoAbonado'))
            fechaPagoCuota = getDatetimeFromString(self.request.get('fechaPagoCuota'))
            observacion = self.request.get('txtObservaciones')
            keyIdVale = self.request.get('keyIdVale')
            rsVale = db.get(keyIdVale)
            rsVale.numeroCuotasPagadas = rsVale.numeroCuotasPagadas + numeroCuotasPagadas
            keyIdAfiliado = self.request.get('keyIdAfiliado')
            rsAfiliado = db.get(keyIdAfiliado)
            if rsAfiliado.montoSueldoNeto >= montoAbonado:
                rsAfiliado.montoSueldoNeto = rsAfiliado.montoSueldoNeto - montoAbonado
                actualizarAfiliado(rsAfiliado)
            else:
                raise SIGSException('El sueldo neto disponible del afiliado no es suficiente para cubrir el pago de la cuota especificada')
            
            if rsAfiliado.deuda >= montoAbonado:
                rsAfiliado.deuda = rsAfiliado.deuda - montoAbonado
                actualizarAfiliado(rsAfiliado)
            else:
                raise SIGSException('La deuda del afiliado no es suficiente para ser cubierta por el pago de la cuota especificada')
            
            insertarAccesoServicio(rsAfiliado, updateValePorServicio(rsVale), numeroCuotasPagadas, montoAbonado, 
                                   fechaPagoCuota, observacion)
            
            dictJson = {'responseStatus':'OK'}
            jsona = json.dumps(dictJson)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)


class JsonHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        radio = self.request.get('radio')
        listaResponse = []
        if opcion == 'contabilidad':
            if radio == 'totalmentePagados':
                rsAccesoServicioContraidoMesActual = obtenerAccesoServicioContraidoMesActual()
                for accesoServicio in rsAccesoServicioContraidoMesActual:
                    if accesoServicio.vale.numeroCuotasPagadas == accesoServicio.vale.numeroCuotas:
                        listaResponse.append(
                                              {
                                              'keyId':str(accesoServicio.key()),
                                              'reciboSueldoNro':accesoServicio.vale.reciboSueldoNro,
                                              'nombreAfiliado': accesoServicio.afiliado.usuario.primerApellido +' '+accesoServicio.afiliado.usuario.segundoApellido +', '+accesoServicio.afiliado.usuario.primerNombre +' '+accesoServicio.afiliado.usuario.segundoNombre,
                                              'numeroAutorizacion':accesoServicio.vale.numeroAutorizacion,
                                              'nombreServicio':accesoServicio.vale.servicio.nombre,
                                              'numeroCuotas':accesoServicio.vale.numeroCuotas,
                                              'resumenCuotas':str(accesoServicio.vale.numeroCuotasPagadas) +'/'+ str(accesoServicio.vale.numeroCuotas),
                                              'monto':accesoServicio.vale.monto
                                              }
                                             )            
            if radio == 'parcialmentePagados':
                rsAccesoServicioContraidoMesActual = obtenerAccesoServicioContraidoMesActual()
                for accesoServicio in rsAccesoServicioContraidoMesActual:
                    if accesoServicio.vale.numeroCuotasPagadas != accesoServicio.vale.numeroCuotas:
                        listaResponse.append(
                                              {
                                              'keyId':str(accesoServicio.key()),
                                              'reciboSueldoNro':accesoServicio.vale.reciboSueldoNro,
                                              'nombreAfiliado': accesoServicio.afiliado.usuario.primerApellido +' '+accesoServicio.afiliado.usuario.segundoApellido +', '+accesoServicio.afiliado.usuario.primerNombre +' '+accesoServicio.afiliado.usuario.segundoNombre,
                                              'numeroAutorizacion':accesoServicio.vale.numeroAutorizacion,
                                              'nombreServicio':accesoServicio.vale.servicio.nombre,
                                              'numeroCuotas':accesoServicio.vale.numeroCuotas,
                                              'resumenCuotas':str(accesoServicio.vale.numeroCuotasPagadas) +'/'+ str(accesoServicio.vale.numeroCuotas),
                                              'monto':accesoServicio.vale.monto
                                              }
                                             )
            if radio == 'todo':
                rsAccesoServicioContraidoMesActual = obtenerAccesoServicioContraidoMesActual()
                for accesoServicio in rsAccesoServicioContraidoMesActual:
                    listaResponse.append(
                                          {
                                          'keyId':str(accesoServicio.key()),
                                          'reciboSueldoNro':accesoServicio.vale.reciboSueldoNro,
                                          'nombreAfiliado': accesoServicio.afiliado.usuario.primerApellido +' '+accesoServicio.afiliado.usuario.segundoApellido +', '+accesoServicio.afiliado.usuario.primerNombre +' '+accesoServicio.afiliado.usuario.segundoNombre,
                                          'numeroAutorizacion':accesoServicio.vale.numeroAutorizacion,
                                          'nombreServicio':accesoServicio.vale.servicio.nombre,
                                          'numeroCuotas':accesoServicio.vale.numeroCuotas,
                                          'resumenCuotas':str(accesoServicio.vale.numeroCuotasPagadas) +'/'+ str(accesoServicio.vale.numeroCuotas),
                                          'monto':accesoServicio.vale.monto
                                          }
                                         )
        jsona = json.dumps(listaResponse)
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(jsona)

class CronTasksHandler(RenderResponseHandler):
    def get(self):
        logging.info('Estamos en CronTasksHandler. La hora es:%s'%str(datetime.datetime.now()))
        #vamos a setear a False el atributo isMontoSueldoNetoActualizado de la tabla Afiliado
        _rsAfliado = Afiliado.all()
        for afiliado in _rsAfliado:
            afiliado.isMontoSueldoNetoActualizado = False
            afiliado.montoSueldoNeto = float(0)
            afiliado.reciboSueldoNro = 0
            actualizarAfiliado(afiliado)

class ImagenHandler(webapp2.RequestHandler):
    def get(self):
        try:
            rsRequest = db.get(self.request.get("img_id"))
            if rsRequest.imagen:
                #TODO porque esto anda aun si la imagen no es png?
                self.response.headers['Content-Type'] = "image/png"
                self.response.out.write(str(rsRequest.imagen))
            else:
                self.response.out.write("Sin imagen")
        except:
            tb = traceback.format_exc()
            ErrorLog(descripcion = str(tb)).put()
            self.doRender('error_page.html', {'mensaje':tb})
            
class ConversionHandler(RenderResponseHandler):
    def get(self):
        opcion = self.request.get('opcion')
        listaMeses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        if opcion == 'afiliadoDetalle':
            keyId = self.request.get('keyId')
            rsAfiliado = db.get(keyId)
            rsDatosLaborales = obtenerDatosLaborales(None, rsAfiliado)
            rsAfiliadoServicio = obtenerAfiliadoServicio(rsAfiliado)
            diccio = {'rsAfiliado':rsAfiliado,'rsDatosLaborales':rsDatosLaborales,
                                                     'rsAfiliadoServicio':rsAfiliadoServicio}
            template = jinja_environment.get_template('afiliado_detalle_html.html')
            outstr = template.render(diccio)
            asset = conversion.Asset("text/html", outstr, "test.html")
            conversion_obj = conversion.Conversion(asset, "application/pdf")
        
            result = conversion.convert(conversion_obj)
        
            if result.assets:
                for asset in result.assets:
                    self.response.headers.add_header('Content-Type', 'application/pdf')
                    self.response.headers.add_header('Content-Disposition', 'attachment; filename=test.pdf')
                    self.response.out.write(asset.data)
            else:
                self.doRender('error_page.html', {'mensaje':str(result.error_text)})
                #handleError(result.error_code, result.error_text)            
        elif opcion=='historialToPdf':
            anho = int(self.request.get('anho'))
            mes = listaMeses.index(self.request.get('mes'))+1#obtenemos la posicion en la lista del mes  
            rsAccesoServicio = obtenerAccesoServicioMesParametro(anho, mes)
            stringTitulo = self.request.get('mes')+'/'+str(anho)
            totalPagosMesActual = 0
            for pago in rsAccesoServicio:
                totalPagosMesActual += float(pago.montoAbonado) 
            
            diccio = {'rsAccesoServicio':rsAccesoServicio,'stringTitulo':stringTitulo,
                                                     'totalPagosMesActual':totalPagosMesActual}
            template = jinja_environment.get_template('historial_vale_html.html')
            outstr = template.render(diccio)
            asset = conversion.Asset("text/html", outstr, "test.html")
            conversion_obj = conversion.Conversion(asset, "application/pdf")
        
            result = conversion.convert(conversion_obj)
        
            if result.assets:
                for asset in result.assets:
                    self.response.headers.add_header('Content-Type', 'application/pdf')
                    self.response.headers.add_header('Content-Disposition', 'attachment; filename=test.pdf')
                    self.response.out.write(asset.data)
            else:
                self.doRender('error_page.html', {'mensaje':str(result.error_text)})
                #handleError(result.error_code, result.error_text)            

class AjaxRequestHandler(webapp2.RequestHandler):
    def get(self):
        opcion = self.request.get('opcion')
        if opcion == 'obtenerSedeKeyId':
            keyId = self.request.get('keyId')
            rsSede = db.get(keyId)
            diccionarioSede = {'nombre':rsSede.nombre,'telefono':rsSede.telefono, 'descripcion':rsSede.descripcion}
            jsona = json.dumps(diccionarioSede)
            self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
            self.response.out.write(jsona)

class MainPage(RenderResponseHandler):
    def get(self):
        #si es una direccion valida la que se pasa en el request, se renderea esa pagina
        if self.doRender(self.request.path):
            return
        #si no es una direccion valida, se renderea el index
        self.obtenerPagina('index')
#Utils
def getCurrentUser():
    return users.get_current_user()

#Operaciones BD
def obtenerUsuarioTablaAdminUser():
    return db.Query(AdminUser).filter('user = ', getCurrentUser()).get()

def insertarAdmin(pNombre,pApellido):
    '''Esto compueba que no exista un usuario un usuario registrado con el mismo nombre
    _key_name = pNombre + pApellido
    _obj = AdminUser.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Ya existe un usuario registrado con esos datos...')
    rsUsuario = AdminUser(key_name = _key_name, user = getCurrentUser(), nombre = pNombre, apellido = pApellido)'''
    rsUsuario = AdminUser(user = getCurrentUser(), nombre = pNombre, apellido = pApellido)
    rsUsuario.put()

def obtenerSindicatosPorAdminUsuario(usuario):
    if usuario:
        return usuario.sindicatos.fetch(50)

#Este metodo va a retornar el sindicato seleccuinado actualmente
def obtenerSindicatoActual():
    _rsSession = obtenerSession(pUserAdmin = obtenerUsuarioTablaAdminUser())
    if _rsSession:
        return _rsSession.sindicato

def insertarSindicato(pNombre = None,  
                      pTelefono = None, 
                      pDescripcion = None, 
                      pImagen = None
                      ):
    #imagenResized = images.resize(pImagen,200,200) if pImagen else None
    _adminUser = obtenerUsuarioTablaAdminUser()
    _keyName = _adminUser.user.email() + pNombre
    _obj = Sindicato.get_by_key_name(_keyName)
    if _obj:
        raise SIGSException('Ya registraste un sindicato con ese nombre.')
    sindicato = Sindicato(key_name = _keyName, nombre = pNombre, telefono = pTelefono, 
                          adminUser = _adminUser, descripcion = pDescripcion,
                          imagen = db.Blob(pImagen)
                          )
    return sindicato.put()
    
def insertarSede(pNombre = None, 
                 pTelefono = None, 
                 pSedePrincipal = None, 
                 pDescripcion = None,
                 pFechaRegistro = None, 
                 pDireccion = None):
    _sindicato = obtenerSindicatoActual()
    _key_name = _sindicato.nombre + pNombre
    _obj = Sede.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Ya existe una sede registrada con ese nombre...')
    sede = Sede(key_name = _key_name,
                nombre = pNombre, 
                principal = pSedePrincipal, 
                telefono = pTelefono,  
                descripcion = pDescripcion,
                fechaRegistro = pFechaRegistro,
                sindicato = _sindicato,
                direccion = pDireccion)
    return sede.put()    
    
def insertarServicio(pNombre = None,
                     pDescripcion = None,
                     pCodigoDescuento = None,
                     pObservaciones = None):
    _sindicato = obtenerSindicatoActual()
    _key_name = _sindicato.nombre + pNombre
    _obj = Servicio.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Ya existe un servicio registrado con ese nombre...')
    _servicio = Servicio(
                        key_name = _key_name,
                        nombre = pNombre, 
                        descripcion = pDescripcion,
                        codigoDescuento = pCodigoDescuento, 
                        observaciones = pObservaciones, 
                        sindicato = obtenerSindicatoActual()
                        )
    return _servicio.put()

def insertarEntidadConvenio(
                            pNombre = None,
                            pTipoDeEmpresa = None,
                            pTelefonoEmpresa = None,
                            pFechaCreacion = None,
                            pFechaExpiracion = None,
                            pDireccion = None,
                            pCondicionesConvenio = None,
                            pObservaciones = None
                            ):
    
    _entidadConvenio = EntidadConvenio(
                                       nombre = pNombre,
                                       tipoDeEmpresa = pTipoDeEmpresa,
                                       telefonoEmpresa = pTelefonoEmpresa,
                                       fechaCreacion = pFechaCreacion,
                                       fechaExpiracion = pFechaExpiracion,
                                       direccion = pDireccion,
                                       condicionesConvenio = pCondicionesConvenio,
                                       observaciones = pObservaciones
                                       )
    return _entidadConvenio.put()

def insertarEntidadConvenioSindicato(
                                     pEntidadConvenio = None,
                                     pSindicato = None
                                     ):
    _sindicato = obtenerSindicatoActual()
    _key_name = _sindicato.nombre + db.get(pEntidadConvenio).nombre
    _obj = EntidadConvenioSindicato.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Una entidad convenio con el mismo nombre ya fue vinculada con el sindicato...')
    _entidadConvenioSindicato = EntidadConvenioSindicato(
                                                         key_name = _key_name,
                                                         entidadConvenio = pEntidadConvenio,
                                                         sindicato = _sindicato
                                                         )
    return _entidadConvenioSindicato.put()

def insertarDireccion(pCalle = None,
                      pNumeroCalle = None,
                      pMunicipio = None,
                      pProvincia = None,
                      pLocalidad = None,
                      pCodigoPostal = None,
                      pPiso = None,
                      pDpto = None
                      ):
    _direccion = Direccion(calle = pCalle,
                           numeroCalle = pNumeroCalle,
                           municipio = pMunicipio,
                           provincia = pProvincia,
                           localidad = pLocalidad,
                           codigoPostal = pCodigoPostal,
                           piso = pPiso,
                           dpto = pDpto
                           )
    return _direccion.put()

def insertarUsuario(
                    pPrimerNombre = None,
                    pSegundoNombre = None, 
                    pPrimerApellido = None,
                    pSegundoApellido = None,
                    pTelefono = None,
                    pTelefonoReferencia = None,
                    pDescripcion = None,
                    pFechaNacimiento = None,
                    pLugarNacimiento = None,
                    pNacionalidad = None,
                    pDocumento = None,
                    pSexo = None,
                    pCorreoElectronico = None,
                    pFuncion = None,       
                    pObservacion = None,
                    pDireccion = None,
                    pSindicato = None                
                    ):
    _key_name = pDocumento
    _obj =  Usuario.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Ya existe un usuario registrado con ese documento...')
    _usuario = Usuario(key_name = pDocumento,
                       primerNombre = pPrimerNombre,
                       segundoNombre = pSegundoNombre, 
                       primerApellido = pPrimerApellido,
                       segundoApellido = pSegundoApellido,
                       telefono = pTelefono,
                       telefonoReferencia = pTelefonoReferencia,
                       descripcion = pDescripcion,
                       fechaNacimiento = pFechaNacimiento,
                       lugarNacimiento = pLugarNacimiento,
                       nacionalidad = pNacionalidad,
                       documento = pDocumento,
                       sexo = pSexo,
                       correoElectronico = pCorreoElectronico,
                       funcion = pFuncion,    
                       observacion = pObservacion,
                       direccion = pDireccion,
                       sindicato = pSindicato)
    return _usuario.put()


def insertarEncargadoSede(pUsuario = None, pSede = None):
    _encargadoSede = EncargadoSede(usuario = pUsuario, sede = pSede)
    return _encargadoSede.put()

def insertarPersonaReferenciaEntidadConvenio(pUsuario = None, pEntidadConvenio = None):
    _personaReferenciaEntidadConvenio = PersonaReferenciaEntidadConvenio(usuario = pUsuario, entidadConvenio = pEntidadConvenio)
    return _personaReferenciaEntidadConvenio.put()

def insertarLugarPrestacionServicio(
                                    pNombre = None,
                                    pTelefono = None,
                                    pObservacion = None,
                                    pDireccion = None
                                    ):
    _lugarPrestacionServicio = LugarPrestacionServicio(
                                                       nombre = pNombre,
                                                       telefono = pTelefono,
                                                       observacion = pObservacion,
                                                       direccion = pDireccion
                                                       )
    return _lugarPrestacionServicio.put()


def insertarLugarPrestacionServicioSindicato(
                                             pLugarPrestacionServicio = None,
                                             pSindicato = None
                                             ):    
    _sindicato = obtenerSindicatoActual()
    rsLugarPrestacionServicio = db.get(pLugarPrestacionServicio)
    _key_name = _sindicato.nombre + rsLugarPrestacionServicio.nombre
    _obj = LugarPrestacionServicioSindicato.get_by_key_name(_key_name)
    if _obj:
        raise SIGSException('Ya existe un lugar de prestacion de servicios registrado con esos datos...')
    
    _lugarPrestacionServicioSindicato = LugarPrestacionServicioSindicato(
                                                                         key_name = _key_name,
                                                                         lugarPrestacionServicio = pLugarPrestacionServicio,
                                                                         sindicato = _sindicato                                                                          
                                                                         )
    return _lugarPrestacionServicioSindicato.put()

def insertarServicioEntidadConvenio(
                                    pServicio = None,
                                    pEntidadConvenio = None,
                                    pLugarPrestacion = None
                                    ):
    _key_name = pServicio.nombre + pEntidadConvenio.nombre + pLugarPrestacion.nombre
    _obj = ServicioEntidadConvenio.get_by_key_name(_key_name)
    if(_obj):
        raise SIGSException("Ya existe vinculada una Entidad Prestadora con esa Direccion")
    _servicioEntidadConvenio = ServicioEntidadConvenio(
                                                       key_name = _key_name,
                                                       servicio = pServicio,
                                                       entidadConvenio = pEntidadConvenio,
                                                       lugarPrestacionServicio = pLugarPrestacion
                                                       )

    return _servicioEntidadConvenio.put()

def insertarEntidadLaboral(
                           pNombre = None,
                           pTipoDeEmpresa = None,
                           pTelefonoEmpresa = None,
                           pCuitEmpleador = None,
                           pDireccion = None,
                           pNumeroSeguridadSocial = None
                           ):
    _rsEntidadLaboral = EntidadLaboral(
                                       nombre = pNombre,
                                       tipoDeEmpresa = pTipoDeEmpresa,
                                       telefonoEmpresa = pTelefonoEmpresa,
                                       cuitEmpleador = pCuitEmpleador,
                                       direccion = pDireccion,
                                       numeroSeguridadSocial = pNumeroSeguridadSocial
                                       )
    return _rsEntidadLaboral.put()


def insertarAfiliado(pUsuario = None, 
                     pCarnet = None, 
                     pFechaRegistro = None, 
                     pCategoriaProfesional = None, 
                     pLugarDeEstudio = None, 
                     pEstadoCivil = None, 
                     pParentesco = None, 
                     pAntiguedadLaboral = None, 
                     pNumeroSuscripcion = None,
                     pCategoriaSuscripcion = None,
                     pSede = None,
                     pMontoSueldoNeto = None,
                     pDeuda = None):
    _rsAfiliado = Afiliado(
                            usuario = pUsuario, 
                            carnet = pCarnet,
                            fechaRegistro = pFechaRegistro,
                            categoriaProfesional = pCategoriaProfesional, 
                            lugarDeEstudio = pLugarDeEstudio,
                            estadoCivil = pEstadoCivil,
                            parentesco = pParentesco,
                            antiguedadLaboral = pAntiguedadLaboral, 
                            numeroSuscripcion = pNumeroSuscripcion, 
                            categoriaSuscripcion = pCategoriaSuscripcion, 
                            sede = pSede,
                            montoSueldoNeto = pMontoSueldoNeto,
                            deuda = pDeuda 
                          )
    return _rsAfiliado.put()

def actualizarAfiliado(pAfiliado = None):
    return pAfiliado.put()

def insertarCargaFamiliar(pUsuario = None, pAfiliadoTitular = None, pParentesco = None):
    _rsCargaFamiliar = CargaFamiliar(
                                     usuario = pUsuario,
                                     afiliadoTitular = pAfiliadoTitular,
                                     parentesco = pParentesco
                                     )
    return _rsCargaFamiliar.put()
    

def insertarDatosLaborales(
                           pEntidadLaboral = None, 
                           pAfiliado = None,
                           pOcupacion = None,
                           pFechaDeIngreso = None, 
                           pCargo = None,
                           pDepartamento= None,
                           pSueldoBase = None,
                           pTipoContrato = None,
                           pContacto = None
                           ):
    _rsDatosLaborales = DatosLaborales(
                                       entidadLaboral = pEntidadLaboral, 
                                       afiliado = pAfiliado,
                                       ocupacion = pOcupacion,
                                       fechaDeIngreso = pFechaDeIngreso,
                                       cargo = pCargo,
                                       departamento= pDepartamento,
                                       sueldoBase = pSueldoBase,
                                       tipoContrato = pTipoContrato,
                                       contacto =pContacto
                                       )  
    return _rsDatosLaborales.put()

def insertarAfiliadoServicio(
                                pAfiliado = None,  
                                pServicio = None, 
                                pObservacion = None, 
                                pEstado = None
                                ):
    #_key_name = pAfiliado.key()+pServicio.key()
    #_obj = AfiliadoServicio.get_by_key_name(_key_name)
    #if(_obj):
    #   raise SIGSException("El afiliado ya fue vinculado con ese servicio")
    _rsAfiliadoServicio = AfiliadoServicio(
                                           #key_name = _key_name,
                                           afiliado = pAfiliado,  
                                           servicio = pServicio, 
                                           observacion = pObservacion, 
                                           estado = pEstado)
    return _rsAfiliadoServicio.put()


def insertarValeServicio(
                            pMonto = None,
                            pNumeroCuotas = None, 
                            pListaLugaresPrestacionServicio = None, 
                            pFechaPrestacion = None,
                            pObservaciones = None,
                            pNumeroAutorizacion = None,
                            pServicio = None,
                            pReciboSueldoNro = None,
                            pNumeroCuotasPagadas = None
                           ):
    _rsValeServicio = ValePorServicio( 
                                      monto = pMonto,
                                      numeroCuotas = pNumeroCuotas,
                                      listaLugaresPrestacionServicio = pListaLugaresPrestacionServicio, 
                                      fechaPrestacion = pFechaPrestacion,
                                      observaciones = pObservaciones,
                                      numeroAutorizacion = pNumeroAutorizacion,
                                      servicio = pServicio, 
                                      reciboSueldoNro = pReciboSueldoNro,
                                      numeroCuotasPagadas = pNumeroCuotasPagadas
                                      )
    return _rsValeServicio.put()

def insertarAccesoServicio(
                              pAfiliado = None,
                              pVale = None,
                              pCuotaPagada = None,
                              pMontoAbonado = None,
                              pFechaPagoCuota = None,
                              pObservacion = None
                             ):
    _rsAccesoServicio = AccesoServicio(
                                       afiliado = pAfiliado,
                                       vale = pVale,
                                       cuotaPagada = pCuotaPagada,
                                       montoAbonado = pMontoAbonado,
                                       fechaPagoCuota = pFechaPagoCuota,
                                       observacion = pObservacion
                                       )
    return _rsAccesoServicio.put()

def insertarSession(pUserAdmin = None, 
                              pSindicato = None, 
                              pImagen = None):
    _rsSession = Session(user=pUserAdmin,
                         sindicato = pSindicato,
                         imagen = pImagen)
    return _rsSession.put()


def obtenerEncargadosSede(pSede = None):
    #return db.GqlQuery("SELECT * FROM EncargadoSede WHERE sede IN :1",obtenerListaSedesPorSindicato())
    _rsEncargado = db.Query(EncargadoSede).filter('sede = ', pSede).get()
    return _rsEncargado

def updateSede(rsSede, pNombre = None, pDireccion = None, pTelefono = None, 
               pEncargado = None, pTelefenoEncargado = None, pDescripcion = None):
    if pNombre is not None: rsSede.nombre = pNombre 
    if pDireccion is not None: rsSede.direccion = pDireccion
    if pTelefono is not None: rsSede.telefono = pTelefono
    if pEncargado is not None: rsSede.encargado = pEncargado
    if pTelefenoEncargado is not None: rsSede.telefonoEncargado = pTelefenoEncargado
    if pDescripcion is not None: rsSede.descripcion = pDescripcion
    db.put(rsSede)
    
def updateServicio(rsServicio,
                   pDescripcion = None,
                   pPrestador = None,
                   #pCondiciones = None,
                   pFechaExpiracion = None, 
                   pPrestadoEn = None,
                   pPersonaReferencia = None,
                   pTelefonoPersonaReferencia = None):
    if pDescripcion is not None: rsServicio.descripcion = pDescripcion
    if pPrestador is not None: rsServicio.prestador = pPrestador
    if pFechaExpiracion is not None: rsServicio.fechaExpiracion = pFechaExpiracion
    if pPrestadoEn is not None: rsServicio.prestadoEn = pPrestadoEn
    if pPersonaReferencia is not None: rsServicio.personaReferencia = pPersonaReferencia
    if pTelefonoPersonaReferencia is not None: rsServicio.telefonoPersonaReferencia = pTelefonoPersonaReferencia
    db.put(rsServicio)

def updateEncargadoSede(pEncargadoSede):
    return db.put(pEncargadoSede)
    
def updateValePorServicio(pValePorServicio):
    return db.put(pValePorServicio)    

def obtenerListaSedesPorSindicato():
    _sindicato = obtenerSindicatoActual()
    if _sindicato:
        return db.Query(Sede).filter('sindicato = ', _sindicato).fetch(50)
    else:
        return None
    
def obtenerPersonaReferenciaEntidadConvenio(pEntidadConvenio = None):
    _rsPersonaReferenciaEntidadConvenio = db.Query(PersonaReferenciaEntidadConvenio).filter('entidadConvenio = ', pEntidadConvenio).fetch(50)
    return _rsPersonaReferenciaEntidadConvenio

def obtenerListaServiciosPorSindicato():
    _sindicato = obtenerSindicatoActual()
    if _sindicato:
        return _sindicato.servicios.fetch(50) 
    else:
        return None
    
def obtenerUsuariosPorSindicato():
    _sindicato = obtenerSindicatoActual()
    return _sindicato.usuarios.fetch(200)

def obtenerEntidadConvenioRelacionadaSindicato():
    _sindicato = obtenerSindicatoActual()
    _entidadConvenioSindicato = db.Query(EntidadConvenioSindicato).filter('sindicato = ', _sindicato).fetch(50)
    _listaEntidadesConvenio = []
    for _entidadConvenio in _entidadConvenioSindicato:
        _listaEntidadesConvenio.append(_entidadConvenio.entidadConvenio)
    return _listaEntidadesConvenio

def obtenerLugarPrestacionServicioRelacionadoSindicato():
    _sindicato = obtenerSindicatoActual()
    _lugarPrestacionServicioSindicato = db.Query(LugarPrestacionServicioSindicato).filter('sindicato = ', _sindicato).fetch(50)
    _listaLugarPrestacionServicio = []
    for lugar in _lugarPrestacionServicioSindicato:
        _listaLugarPrestacionServicio.append(lugar.lugarPrestacionServicio)
    return _listaLugarPrestacionServicio

def obtenerServicioEntidadConvenioPorSindicato(pServicio = None, pEntidadConvenio = None):
    if pServicio is not None:
        rsServicioEntidadConvenio = pServicio.servicioEntidadConvenio
    elif pEntidadConvenio is not None:
        rsServicioEntidadConvenio = pEntidadConvenio.servicioEntidadConvenio
    elif pServicio is not None and pEntidadConvenio is not None:
        rsServicioEntidadConvenio = db.Query(ServicioEntidadConvenio).filter("servicio = ", pServicio).filter("entidadConvenio = ", pEntidadConvenio).fetch(50)
    else:
        return None
    return rsServicioEntidadConvenio

'''
obtener el resultset de ServicioEntidadConvenio de acuerdo al servicio pasado como parametro.
De ahi obtener la lista de entidades convenio no repetidas.
Por cada entidad convenio, obtener la lista de lugares de prestacion servicio.
Recorrer la lista de entidades convenio no repetidas y por cada una compararla con
cada entidadConvenio del resultset de ServicioEntidadConvenio. Si coinciden,
almacenar ese valor en un LISTA DE LUGARES DE PRESTACION DE SERVICIO.
Al final, retornar una lista de diccionarios que contenga como primer elemento una entidadConvenio y 
como segundo elemento la lista de lugares de prestacionDeServicio que le corresponde
'''
def obtenerListaEntidadesYLugaresPorEntidad(pServicio = None):
    _rsServicioEntidadConvenio = obtenerServicioEntidadConvenioPorSindicato(pServicio)
    _listaEntidadesConvenio = []
    _diccLugaresPrestacionServicioPorEntidadConvenio = []
    for entidad in _rsServicioEntidadConvenio:
        _listaEntidadesConvenio.append(entidad.entidadConvenio.key())
    #para limpiar la lista, obteniendo las entidades NO repetidas
    _listaEntidadesConvenio = set(_listaEntidadesConvenio)
    #
    for entidad in _listaEntidadesConvenio:
        rsEntidadConvenio = db.get(entidad)#vuelvo a obtener EntidadConvenio con el iterador entidad solo almacena el key de esa EntidadConvenip
        _listaLugaresPrestacionServicio = []
        for en in _rsServicioEntidadConvenio:
            if entidad == en.entidadConvenio.key():
                _listaLugaresPrestacionServicio.append(en.lugarPrestacionServicio)
        _diccLugaresPrestacionServicioPorEntidadConvenio.append({'entidadConvenio':rsEntidadConvenio,'lugaresPrestacionServicio':_listaLugaresPrestacionServicio})
    
    return _diccLugaresPrestacionServicioPorEntidadConvenio
    
    
def obtenerEntidadesLaborales():
    return EntidadLaboral.all().fetch(50)


def obtenerAfiliados(pParentesco = None):
    _sindicato = obtenerSindicatoActual()
    #obenetmos los usuarios vinculados al sindicato
    rsUsuarios = db.Query(Usuario).filter('sindicato = ', _sindicato).fetch(50)
    #obtenemos todos los afiliados vinculados a estos usuarios
    if pParentesco == 'TITULAR':
       return db.Query(Afiliado).filter('usuario IN ', rsUsuarios).filter('parentesco = ','TITULAR').fetch(50)
    elif pParentesco == 'CARGA_FAMILIAR':
       return db.Query(Afiliado).filter('usuario IN ', rsUsuarios).filter('parentesco = ','CARGA_FAMILIAR').fetch(50)
    else:
       return db.Query(Afiliado).filter('usuario IN ', rsUsuarios).fetch(50)
    
def obtenerAfiliadosPorSede(pSede):
    return db.Query(Afiliado).filter('sede = ', pSede).fetch(50)
    
       
def obtenerDatosLaborales(pEntidadLaboral = None, pAfiliado = None):
    if pEntidadLaboral is not None and pAfiliado is None:
        return db.Query(DatosLaborales).filter('entidadLaboral = ', pEntidadLaboral).fetch(50)
    elif pAfiliado is not None and pEntidadLaboral is None:
        return db.Query(DatosLaborales).filter('afiliado = ', pAfiliado).fetch(50)
    elif pEntidadLaboral is not None and pAfiliado is not None:
        return db.Query(DatosLaborales).filter('entidadLaboral = ', pEntidadLaboral).filter('afiliado = ', pAfiliado).filter(50)
    
def obtenerAfiliadoServicio(pAfiliado=None, pServicio = None):
    if pAfiliado is not None and pServicio is None:
        return db.Query(AfiliadoServicio).filter('afiliado = ', pAfiliado).fetch(50)
    elif pServicio is not None and pServicio is None:
        return db.Query(AfiliadoServicio).filter('servicio = ', pServicio).fetch(50)
    elif pServicio is not None and pAfiliado is not None:
        return db.Query(AfiliadoServicio).filter('afiliado = ', pAfiliado).filter('servicio = ', pServicio).fetch(50)

#retorna todos los AccesoServicio con vales del mes actual, PERO hace una distincion
#haciendo que los Vales NO se repitan.
def obtenerAccesoServicioVigentesMesesAnteriores():
    _rsAfiliados = obtenerAfiliados()
    _mesActual = datetime.datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _rsAccesoServicio = db.Query(AccesoServicio).filter('afiliado IN ', _rsAfiliados).fetch(50)
    _rsAccesoServicio_ValeNoRepetido = []
    _rsAccesoServicio_ValeNoRepetido_Vale = []
    for _result in _rsAccesoServicio:
        if _result.vale.fechaPrestacion < _mesActual and (_result.vale.numeroCuotasPagadas < _result.vale.numeroCuotas):
            if _result.vale.key() not in _rsAccesoServicio_ValeNoRepetido_Vale:
                _rsAccesoServicio_ValeNoRepetido_Vale.append(_result.vale.key())
                _rsAccesoServicio_ValeNoRepetido.append(_result)
    return _rsAccesoServicio_ValeNoRepetido

#retorna todos los AccesoServicio con vales del mes actual, PERO hace una distincion
#haciendo que los Vales NO se repitan.
def obtenerAccesoServicioContraidoMesActual():
    _rsAfiliados = obtenerAfiliados()
    _mesActual = datetime.datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    _rsAccesoServicio = db.Query(AccesoServicio).filter('afiliado IN ', _rsAfiliados).fetch(50)
    _rsAccesoServicio_ValeNoRepetido = []
    _rsAccesoServicio_ValeNoRepetido_Vale = []
    for _result in _rsAccesoServicio:
        if _result.vale.fechaPrestacion >= _mesActual:
            if _result.vale.key() not in _rsAccesoServicio_ValeNoRepetido_Vale:
                _rsAccesoServicio_ValeNoRepetido_Vale.append(_result.vale.key())
                _rsAccesoServicio_ValeNoRepetido.append(_result)
    return _rsAccesoServicio_ValeNoRepetido
        
def obtenerAccesoServicioPagosMesActual():
    _rsAfiliados = obtenerAfiliados()
    _mesActual = datetime.datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return db.Query(AccesoServicio).filter('afiliado IN ', _rsAfiliados).filter('fechaPagoCuota >= ', _mesActual).fetch(50)

def obtenerAccesoServicioMesParametro(pAnho, pMes):
    _rsAfiliados = obtenerAfiliados()
    _fechaDesde = datetime.date(pAnho,pMes,1)
    #_fechaHasta = _fechaDesde + relativedelta(months=+1)#incrementamos un mes
    _fechaHasta = getDate(1, pMes+1, pAnho)
    return db.Query(AccesoServicio).filter('afiliado IN ', _rsAfiliados).filter('fechaPagoCuota >=', _fechaDesde).filter('fechaPagoCuota <=', _fechaHasta)
    

#esta funcion retorna fechas incrementadas. Se usa para aumentar un mes. No
#es precisa, porque no anda para los meses con dias distintos, pero 
#es un reemplazo al timedelta    
def getDate(date, month, year):
    if month > 12:
        year += 1
        month -= 12
    return datetime.date(year, month, date)
    

def obtenerSession(pUserAdmin = None, 
                              pSindicato = None):
    try:
        if pUserAdmin and pSindicato is None:
            return db.Query(Session).filter('user = ',pUserAdmin).get()
        elif pSindicato and pUserAdmin is None:
            rs = db.Query(Session).filter('sindicato = ', pSindicato).get() 
            return rs
        else:
            return db.Query(Session).filter('user = ',pUserAdmin).filter('sindicato = ', pSindicato).get()
    except Exception as e:
        logging.info(e)
    
    

'''
def obtenerTotalCuotasAPagarPorVale(rsVale = None):
    rsAccesoServicio = db.Query(AccesoServicio).filter('vale = ', rsVale).fetch(50)
    maxCuotas = rsVale.numeroCuotas
    cantidadCuotasPorPagadar = maxCuotas 
    #se resta la cantidad de cuotas del vale por la cantidad de cuotas pagadas
    if rsAccesoServicio:
        cantidadCuotasPorPagadar =  maxCuotas - len(rsAccesoServicio)
    return cantidadCuotasPorPagadar
'''
    
    
def insertarErrorLog(traceback = None):
    ErrorLog(descripcion = str(traceback)).put()

def setSedesNoSedePrincipal():
    _sindicato = obtenerSindicatoActual()
    _rsSedes = _sindicato.sedes.fetch(50)
    if _rsSedes:
        for sede in _rsSedes:
            sede.principal = 'N'
            sede.put()
  
    
def main():
    app = webapp2.WSGIApplication([
                                   ('/procesarPagina',ProcesarPaginasHandler),
                                   ('/registro',RegistroHandler),
                                   ('/sindicato',SindicatoHandler),
                                   ('/sede',SedeHandler),
                                   ('/servicio', ServicioHandler),
                                   ('/entidadConvenio', EntidadConvenioHandler),
                                   ('/lugarPrestacionServicio', LugarPrestacionServicioHandler),
                                   ('/servicioEntidadConvenio',ServicioEntidadConvenioHandler),
                                   ('/entidadLaboral', EntidadLaboralHandler),
                                   ('/afiliado', AfiliadoHandler),
                                   ('/ajaxRequest',AjaxRequestHandler),
                                   ('/servicioAfiliado', ServicioAfiliadoHandler),
                                   ('/valeServicio', ValeServicioHandler),
                                   ('/accesoServicios', AccesoServicioHandler),
                                   ('/json', JsonHandler),
                                   ('/cronTask', CronTasksHandler),
                                   ('/img', ImagenHandler),
                                   ('/conversion', ConversionHandler),
                                   ('/.*', MainPage)
                                   ],debug=True)
    wsgiref.handlers.CGIHandler().run(app)
if __name__ == '__name__':
    main()
    
class SIGSException(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)
    
    
def validateNotEmptyNotNumber(value):
    if value and not is_number(value):
        return True
    return False

def validateNotEmptyIsNumber(value):
    if value and is_number(value):
        return True
    return False


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
    
#esto itera sobre un diccionario y comprueba que todos los elementos tengan el valor OK,
#lo que determina su validez. Si algun valor no cumple la condicion, el diccionario posee 
#valores que no pasaron la validacion. Se lo invoca generalmente antes de una llamada a una
#operacion de BD para que no se inserten valores que no se controlan en la insercion.
def checkDictionaryForValidation(dicc):
    for key, value in dicc.iteritems():
        if value is not "OK":
            return False
    return True


def getInfoMessageByCode(pCodigo, pTexto = None):
    if pCodigo == 45:
        return 'Bienvenido al sistema %s'%(pTexto)
    elif pCodigo == 55:
        return 'El sindicato %s fue registrado con exito'%(pTexto)
    elif pCodigo == 65:
        return 'La sede %s fue registrada con exito'%(pTexto)
    elif pCodigo == 66:
        return 'La sede %s fue eliminada con exito'%(pTexto)
    elif pCodigo == 67:
        return 'La sede %s fue modificada con exito'%(pTexto)
    elif pCodigo == 75:
        return 'El servicio %s fue registrado con exito'%(pTexto)
    elif pCodigo == 85:
        return 'La entidad prestadora de convenio %s fue registrada con exito'%(pTexto)
    elif pCodigo == 95:
        return 'El afiliado %s fue registrado con exito'%(pTexto)
    elif pCodigo == 105:
        return 'Se ha vinculado un nuevo lugar de prestacion del servicio a una entidad prestadora'
def getDatetimeFromString(string):
    try:
        return datetime.datetime.strptime(string,'%d/%m/%Y')
    except:
        return None
    
def validateJsonResponse(jsonDictionary, methodName, *args):
    isValidDictionary = checkDictionaryForValidation(jsonDictionary) 

    responseStatus = "ERR"
    if isValidDictionary:
        try:    
            methodName(*args)
        except SIGSException as e:
            jsonDictionary['errorMessage'] = e.value
        except Exception as e:
            jsonDictionary['errorMessage'] = str(e)
        else:
            jsonDictionary['errorMessage'] = "NONE"
            responseStatus = "OK"
    else:
        jsonDictionary['errorMessage'] = "Verifique los datos invalidos ingresados..."
    jsonDictionary['responseStatus'] = responseStatus
    return json.dumps(jsonDictionary)


def validateJsonResponseNoDumps(jsonDictionary, methodName, *args):
    isValidDictionary = checkDictionaryForValidation(jsonDictionary) 

    responseStatus = "ERR"
    if isValidDictionary:
        try:    
            methodName(*args)
        except SIGSException as e:
            jsonDictionary['errorMessage'] = e.value
        except Exception as e:
            jsonDictionary['errorMessage'] = str(e)
        else:
            jsonDictionary['errorMessage'] = "NONE"
            responseStatus = "OK"
    else:
        jsonDictionary['errorMessage'] = "Verifique los datos invalidos ingresados..."
    jsonDictionary['responseStatus'] = responseStatus
    return jsonDictionary

def verifyNumber(pValue):
    if is_number(pValue):
        return int(pValue)
    else:
        return 0
    
def stringToHash(value):
    return hashlib.md5(value).hexdigest()
