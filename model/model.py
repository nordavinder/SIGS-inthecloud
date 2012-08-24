from google.appengine.ext import db

class AdminUser(db.Model):
    user = db.UserProperty()
    nombre = db.StringProperty(required = True)
    apellido = db.StringProperty(required = True)
    fechaRegistro = db.DateTimeProperty(auto_now_add=True)
    
class Direccion(db.Model):
    calle = db.StringProperty()
    numeroCalle = db.IntegerProperty()
    municipio = db.StringProperty()
    provincia = db.StringProperty()
    localidad = db.StringProperty()
    codigoPostal = db.StringProperty()
    piso = db.StringProperty()
    dpto = db.StringProperty()


class EntidadLaboral(db.Model):
    nombre = db.StringProperty()
    tipoDeEmpresa = db.StringProperty()
    telefonoEmpresa = db.StringProperty()
    cuitEmpleador = db.StringProperty()
    direccion = db.ReferenceProperty(Direccion, collection_name = 'entidadesLaborales')    #esta es una relacion 1-1
    numeroSeguridadSocial = db.StringProperty()

class Sindicato(db.Model):
    nombre = db.StringProperty(required = True)
    telefono = db.StringProperty()
    imagen = db.BlobProperty()
    descripcion = db.StringProperty()
    fechaRegistro = db.DateTimeProperty(auto_now_add=True)
    adminUser = db.ReferenceProperty(AdminUser, collection_name='sindicatos')
    
class Usuario(db.Model):
    primerNombre = db.StringProperty(required = True)
    segundoNombre = db.StringProperty() 
    primerApellido = db.StringProperty(required = True)
    segundoApellido = db.StringProperty()
    fechaRegistro = db.DateTimeProperty(auto_now_add=True)
    telefono = db.StringProperty()
    telefonoReferencia = db.StringProperty()
    descripcion = db.StringProperty()
    fechaNacimiento = db.DateTimeProperty()
    lugarNacimiento = db.StringProperty()
    nacionalidad = db.StringProperty()
    documento = db.StringProperty()
    sexo = db.StringProperty(choices=set(["F","M"]))
    correoElectronico = db.StringProperty()
    funcion = db.StringProperty()    
    observacion = db.StringProperty()
    direccion = db.ReferenceProperty(Direccion, collection_name='usuarios') 
    sindicato = db.ReferenceProperty(Sindicato, collection_name='usuarios')

     
class Sede(db.Model):
    nombre = db.StringProperty()
    principal = db.StringProperty(choices=set(["S","N"]))
    telefono = db.StringProperty()
    descripcion = db.StringProperty()
    fechaRegistro = db.DateTimeProperty()
    sindicato = db.ReferenceProperty(Sindicato, collection_name='sedes')
    direccion = db.ReferenceProperty(Direccion, collection_name = 'sedes')    #esta es una relacion 1-1

class Servicio(db.Model):
    nombre = db.StringProperty()
    descripcion = db.StringProperty()
    observaciones = db.StringProperty()
    codigoDescuento = db.StringProperty()
    sindicato = db.ReferenceProperty(Sindicato, collection_name='servicios')
    

class Afiliado(db.Model):
    usuario = db.ReferenceProperty(Usuario, collection_name='afiliados')
    carnet = db.StringProperty()
    fechaRegistro = db.DateTimeProperty()
    categoriaProfesional = db.StringProperty()#categoria profesional -->Estudios: titulo de mayor nivel
    lugarDeEstudio = db.StringProperty()
    estadoCivil = db.StringProperty(choices=set(["Soltero","Casado","Divorciado","Viudo","Separado"]))
    parentesco = db.StringProperty(choices=set(["TITULAR","CARGA_FAMILIAR"]))
    antiguedadLaboral = db.IntegerProperty()
    numeroSuscripcion = db.IntegerProperty()
    categoriaSuscripcion = db.StringProperty()
    sede = db.ReferenceProperty(Sede, collection_name='afiliados')
    isMontoSueldoNetoActualizado = db.BooleanProperty(default=False)
    montoSueldoNeto = db.FloatProperty()
    deuda = db.FloatProperty()
    reciboSueldoNroMesActual = db.IntegerProperty()
    
class EntidadConvenio(db.Model):
    nombre = db.StringProperty()
    tipoDeEmpresa = db.StringProperty()
    telefonoEmpresa = db.StringProperty()
    fechaCreacion = db.DateTimeProperty()
    fechaExpiracion = db.DateTimeProperty()
    direccion = db.ReferenceProperty(Direccion, collection_name = 'entidadesConvenio')    #esta es una relacion 1-1
    #tipoContrato = db.StringProperty()
    condicionesConvenio = db.StringProperty()
    observaciones = db.StringProperty()

    def toDict(self):
        return {
                'nombre':self.nombre,
                'tipoDeEmpresa': self.tipoDeEmpresa,
                'telefonoEmpresa':self.telefonoEmpresa,
                'fechaCreacion': self.fechaCreacion,
                'fechaExpiracion': self.fechaExpiracion,
                'direccion':self.direccion,
                'condicionesConvenio':self.condicionesConvenio,
                'observaciones':self.observaciones
                }

class LugarPrestacionServicio(db.Model):
    nombre = db.StringProperty()
    telefono = db.StringProperty()
    observacion = db.StringProperty()
    direccion = db.ReferenceProperty(Direccion, collection_name='lugarPrestacionServicio')#entonces, si se quieren 
    #obtener los servivios prestados en una determinada sede, se busca la direccion de la sede nomas.

#M-M
#class SedeServicios(db.Model):
#    sede = db.ReferenceProperty(Sede, collection_name='servicios')
#    servicio = db.ReferenceProperty(Servicio, collection_name='sedes')
#    fechaAgregado = db.DateTimeProperty(auto_now_add=True)

class EntidadConvenioSindicato(db.Model):
    entidadConvenio = db.ReferenceProperty(EntidadConvenio, collection_name='entidadConvenioSindicato')
    sindicato = db.ReferenceProperty(Sindicato, collection_name='entidadConvenioSindicato')
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)
    
class LugarPrestacionServicioSindicato(db.Model):
    lugarPrestacionServicio = db.ReferenceProperty(LugarPrestacionServicio, collection_name='lugarPrestacionServicioSindicato')
    sindicato = db.ReferenceProperty(Sindicato, collection_name='lugarPrestacionServicioSindicato')
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)
    
class PersonaReferenciaEntidadConvenio(db.Model):
    usuario = db.ReferenceProperty(Usuario, collection_name='personaReferenciaEntidadConvenio')
    entidadConvenio = db.ReferenceProperty(EntidadConvenio, collection_name='personaReferenciaEntidadConvenio')
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)

class EncargadoSede(db.Model):
    usuario = db.ReferenceProperty(Usuario, collection_name='encargadoSede')    
    sede=db.ReferenceProperty(Sede, collection_name='encargadoSede')
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)
    
class AfiliadoServicio(db.Model):
    afiliado = db.ReferenceProperty(Afiliado, collection_name='afiliadoServicio')
    servicio = db.ReferenceProperty(Servicio, collection_name='afiliadoServicio')
    observacion = db.StringProperty()
    estado = db.StringProperty()
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)

class CargaFamiliar(db.Model): #Beneficiario por Extencion
    usuario = db.ReferenceProperty(Usuario, collection_name='cargasFamiliares')
    afiliadoTitular = db.ReferenceProperty(Afiliado, collection_name='cargasFamiliares')
    parentesco = db.StringProperty()

    
class ServicioEntidadConvenio(db.Model):
    servicio = db.ReferenceProperty(Servicio, collection_name='servicioEntidadConvenio')
    entidadConvenio = db.ReferenceProperty(EntidadConvenio, collection_name='servicioEntidadConvenio')
    lugarPrestacionServicio = db.ReferenceProperty(LugarPrestacionServicio, collection_name = 'servicioEntidadConvenio')
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)   
    


class ErrorLog(db.Model):
    descripcion = db.StringProperty(multiline=True)
    fechaAgregado = db.DateTimeProperty(auto_now_add = True)
    agregadoPor = db.UserProperty(auto_current_user_add = True)


class Session(db.Model):
    user = db.ReferenceProperty(AdminUser, collection_name='session')
    sindicato = db.ReferenceProperty(Sindicato, collection_name='session' )
    imagen = db.BlobProperty()



#TODO union entre Afiliado y EntidadLaboral. No queria hacer esto, pero hay datos de esta tabla
#que deben almcenarse en alguna parte.
class DatosLaborales(db.Model):
    entidadLaboral = db.ReferenceProperty(EntidadLaboral, collection_name='datosLaborales')
    afiliado = db.ReferenceProperty(Afiliado, collection_name='datosLaborales')
    ocupacion = db.StringProperty(choices=set(["Asalariado","Autonomo","Cooperativista","Parado","Jubilado","Pensionado"]))
    fechaDeIngreso = db.DateTimeProperty()
    cargo = db.StringProperty()
    departamento= db.StringProperty()
    sueldoBase = db.IntegerProperty
    tipoContrato = db.StringProperty(choices=set(["Fijo","Fijo Discontinuo","Tiempo Parcial","Interinidad"]))
    contacto = db.StringProperty()

class ValePorServicio(db.Model):
    servicio = db.ReferenceProperty(Servicio, collection_name='valeServicio')
    monto = db.FloatProperty()
    numeroCuotas = db.IntegerProperty()
    listaLugaresPrestacionServicio = db.StringListProperty()#los lugares en los que puede canjear el vale
    fechaPrestacion = db.DateTimeProperty()
    observaciones = db.StringProperty()
    numeroAutorizacion = db.IntegerProperty()
    reciboSueldoNro = db.IntegerProperty()#se diferencia con el de afiliado, en que este almacena la del mes actual que le corresponde al afiliado
    numeroCuotasPagadas = db.IntegerProperty()
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)
    
class AccesoServicio(db.Model):
    afiliado = db.ReferenceProperty(Afiliado, collection_name='accesoServicio')
    vale = db.ReferenceProperty(ValePorServicio, collection_name='accesoServicio')
    cuotaPagada = db.IntegerProperty()
    montoAbonado = db.FloatProperty()
    fechaPagoCuota = db.DateTimeProperty()
    observacion = db.StringProperty()
    fechaAgregado = db.DateTimeProperty(auto_now_add=True)

'''TODO:
21/06/2012
-ARMAR LAS OPCIONES DEL SISTEMA. Ej: Cargar Afiliado-->datos laborales, carga familiar, 


Entidades
-Usuario
-Sindicato
-Sede
-Servicio
-Afiliado
-Direccion
-EntidadLaboral
-EntidadConvenio
--relaciones---
-SedeServicios
-PersonaReferenciaEntidadConvenio
-EncargadoSede
-AfiliadoServicio
-CargaFamiliar
-ServicioEntidadConvenio
-DatosLaborales


U.C
-Administrar usuario: desde aca podes administrar las personas relacionadas con el sindicato.
    -ALTA:agregar un usuario-> que se permita ingresar los datos de la tabla usuario, y que al final haya un checkbox que diga Afiliado-Otro. Si
    es afiliado, se completan los datos faltantes de afiliado y se inserta en la tabla Afiliado. Si no, que se especifique su funcion 
              en el sindicato, y que se inserte en la tabla Usuario nomas.
        -BAJA-MODIFICACION: se altera de la tabla usuario y de la que corresponda.
    -ESPEC:
        -AFILIADO: idem. Que haya un enlace en la que se seleccione el sindicato, la sede y la empresa y los datos laborales con los 
        que se lo relaciona.
            -Que en la lista de afiliados haya una opcion para suscribirlo a un servicio de la lista que se guardan en AfiliadoServicio.
        -CARGAFAMILIAR: Se completan los datos del afiliado y que haya un checkbox de si es CargaFamiliar o no. Si es, al selecionar el 
        check, que aparezca un fieldset para completar los datos de CargaFamiliar. Que en la parte en la que se completa el campo
        afiliadoTitular, se permita seleccionar un afiliado que sea titular. Si no esta cargado todavia el afiliadoTitular, que aparezca
        un enlace para cargarlo dentro del comboBox. Que el combo aparezca ordenado alfabeticamente. Lo mismo para el campo sindicato.
        -PERSONAREFENCIASERVICIO: que permita ser seleccionada desde la pantalla de carga de servicio.
-Administrar Sindicato: desde aca podes administrar tus sindicatos
    -ALTA: como esta ahora, mas el fieldset direccion.
-Sede: desde aca podes administrar las sedes del sindicato
    -ALTA: que aparezca tambien una opcion para vincular a un usuario como encargado y que eso se almacene en EncargadoSede. 
            -EncargadoSede: que en la pagina de altas, despues de cargar un usuario, aparezca una ventana de carga de usuario que permita
            vincular a la sede creada recientemente con el usuario a crear.
-Servicio: desde aca podes administrar los servicios del sindicato
    -ALTA: se carga el servicio y que en el fin del proceso, se dirija a una pagina que permita vincular ese servicio con un encargado.
    -ADMINISTRACION: 
        -opciones: 
            -Entidad Convenio: Gestion de entidades prestadoras de servicios. Se almacena en EntidadConvenio.
            -ServicioSindicato: permite vincular Servicios con Sindicatos.

NOTAS:
-respetar el esquema de hasta ahora: primero se carga un sindicato, despues los afiliados o servicios.
'''
        
              
