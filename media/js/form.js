$(document).ready(function() {
	$('ul.filter-list').children('li').hide();
	$('ul.filter-list').children(
			'li:nth-child(1), li:nth-child(2), li:nth-child(3), li:nth-child(4), li:nth-child(5)'
			).show();
	$('ul.filter-list')
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

function vansearch_hidefilters (filterlist) {
	filterlist.children('li:nth-child(1), li:nth-child(2), li:nth-child(3), li:nth-child(4), li:nth-child(5)');
}