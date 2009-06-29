$(document).ready(function() {
	$('#q.initial').focus(function() {
		if (this.value == this.defaultValue) {
			this.value = "";
		};
	}).blur(function() {
		if ( !this.value.length ) {
			this.value = this.defaultValue;
		};
	});
	
	$('div.search-cnt img').show();
	$('div.search-cnt input.button').hide();
	$('div.search-cnt img.button').click(function() {
		$('form').submit();
	});
});
