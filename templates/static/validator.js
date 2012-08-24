function validarCampoTextoNotEmpty(inputText, errorMessage){
	if($(inputText).val()==''){
		setFieldAsNotValid(inputText, errorMessage);
		return false;
	}else{
		removeErrorMessage(inputText);
		return true;
	}
}
//valida si un textfield es vacio o, segun el parametro, si es un numero o no.
function validarCampoTexto(inputText, errorMessage, type){
	if($(inputText).val()==''){
		setFieldAsNotValid(inputText, errorMessage);
		return false;
	}else{
		if(type=='number'){
			if(isNaN($(inputText).val())){
				setFieldAsNotValid(inputText, errorMessage);
				return false;
			}
		}
		if(type=='string'){
			if(!isNaN($(inputText).val())){
				setFieldAsNotValid(inputText, errorMessage);
				return false;
			}
		} 
		removeErrorMessage(inputText);
		return true;
	}
}
function validarSelectElement(selectElement, errorMessage){
	if($(selectElement).attr('selected','selected').length){
		setFieldAsNotValid(selectElement, errorMessage);
		return false;
	}else{
		removeErrorMessage(selectElement);
		return true;
		
	}
}

function setFieldAsNotValid(element, errorMessage){
	if ($(element).next('div').length){//esto para que me elimine el elemento siguiente solo si es div.
		$(element).next().remove();
	}
	$(element).after('<div style="margin-left:0px;"><b>'+errorMessage+'</b></div>')
	$(element).addClass('selected');
}

function removeErrorMessage(element){
	if ($(element).next('div').length){
		$(element).next().remove();
		$(element).removeClass('selected');		
	}
}

function validateElementFromJsonResponse(successString,jsonResponseData, element){
	if(jsonResponseData!=null && jsonResponseData != successString){
		setFieldAsNotValid(element, jsonResponseData);
		return false;
	}
	removeErrorMessage(element);
	return true;
}

function markFieldAsNotValid(element){
	$(element).nextAll().remove();
	$(element).addClass('invalid-field');
}

function removeErrorMessageRed(element){
	$(element).nextAll().remove();
	$(element).removeClass('invalid-field');
}


function validateElementFromJsonResponseMarkField(successString,jsonResponseData, element){
	if(jsonResponseData != successString){
		markFieldAsNotValid(element)
		return false;
	}
	$(element).removeClass('invalid-field');
	return true;
}

function showNotification(type, message, timeout,layout){
	$.noty.closeAll();
	noty({force: true, timeout: timeout, layout : layout, text: message, type: type});
}

function validateArray(array, type, message, timeout,layout){
	response = true;
	$.each(array, function(index,item){
		if(!item){
			response = false;
			return;
		}
	});
	if(!response)
		showNotification(type, message, timeout,layout)
	return response;
}

//para mostrar el dialogo on mouseOver
function mostrarDialogo(divElement, aElement, outterFunction){
	var dlg = $(divElement).dialog({
		autoOpen: false,
		draggable: false,
		resizable: false,
		width: 300
	});
	
	$(aElement).mouseover(function() {
		outterFunction($(this));
		dlg.dialog("open");
	}).mousemove(function(event) {
		dlg.dialog("option", "position", {
			my: "left top",
			at: "right bottom",
			of: event,
			offset: "20 20",
			title: "fdfsdfs"
		});
	}).mouseout(function() {
		dlg.dialog("close");
	});
	
}


function construirDialogo(oldDiv, title, pArray){
	var newDiv = $('<div id="dialog" title="'+title+'">');
	$.each(pArray,function(index, item){
		newDiv.append('<p>'+item+'</p>');
	});
	newDiv.append('</div>');
	$(oldDiv).empty();
	$(oldDiv).append(newDiv);
}

function validateSelectedRadio(radio, button, message){
	$(button).click(function(){
		if($(radio).is(':checked')){
			return true;
		}else{
			alert(message);
			return false;
		}		
	});
}

function initSimpleTableSorter(tableElement){
	$.extend( $.fn.dataTable.defaults, {
        "bFilter": false,
        "bPaginate":false,
        "bInfo":false
    } );
	$(tableElement).dataTable();
}

function initFullTableSorter(tableElement){
	$(tableElement).dataTable( {
        "oLanguage": {
            "sLengthMenu": "Mostrar _MENU_ resultados por página",
            "sZeroRecords": "No hay resultados.",
            "sInfo": "Mostrando _START_ a _END_ de _TOTAL_ resultados",
            "sInfoEmpty": "Sin resultados",
            "sSearch":"Buscar",
            "sPrevious":"Anterior",
            "sNext":"Siguiente",
            "sInfoFiltered": "(filtrado sobre _MAX_ entradas totales)",
        }
    } );
}