$(document).ready(function() {
	$('#q').focus(function() {
		if (this.value == this.defaultValue) {
			this.value = "";
		};
	}).blur(function() {
		if ( !this.value.length ) {
			this.value = this.defaultValue;
		};
	});
});
