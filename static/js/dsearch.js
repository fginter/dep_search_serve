function dsearch_ajax_response(json_data,resdiv) {
    var respdata=jQuery.parseJSON(json_data)
    $(resdiv).html(respdata.ret);
    $('.conllu').each(function() {
	Annodoc.embedAnnotation($(this), Annodoc.parseConllU,
				Config.bratCollData);
    });
}

function dsearch_simulate_form(corpus,query,case_sensitive,hits_per_page) {
    $('#query').val(query);
    $('#treeset').val(corpus);
    $('#case').val(case_sensitive);
    $('#hits_per_page').val(hits_per_page);
    dsearch_run_ajax('#inpform','/query','#queryresult');
    window.history.pushState("string", "", "/");
}

function dsearch_run_ajax(frm,path,resdiv) {
    $.ajax({
	    url: $APP_ROOT+path,
	    data: $(frm).serialize(),
	    type: 'POST',
	    success: function(response){
		dsearch_ajax_response(response,resdiv);
	    },
	    error: function(error){
		console.log(error);
	    }
    });
}

//hooks a form frm and result div resdiv to ajax path path
function ahook(frm,button,resdiv,path) {
    console.log("running ahook",frm, resdiv,path);
    $(frm).submit(function(e){
	dsearch_run_ajax(frm,path,resdiv);
	e.preventDefault();
    });
}

/*$(function() {
    $( ".autocomplete" ).autocomplete({
      source: $APP_ROOT+"/autocomplete",
      minLength: 2,
    });
});*/
  

$(function() {ahook('#inpform','#submitquery','#queryresult','/query');});



