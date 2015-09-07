function remove(arr, item) {
      for(var i = arr.length; i--;) {
          if(arr[i] === item) {
              arr.splice(i, 1);
          }
      }
  }

  Array.prototype.sum = function () {
      var total = 0;
      var i = this.length;

      while (i--) {
          total += parseInt(this[i]);
      }

      return total;
  }

Array.prototype.newsum = function(){
	this.reduce(function(pv, cv) { return pv + cv; }, 0);
}

Number.prototype.pad = function(size) {
      var s = String(this);
      while (s.length < (size || 2)) {s = "0" + s;}
      return s;
}
 function tolalHours(login,logout){
 	if(login == '' || login.length < 1 || typeof login != 'string' &&
 	  logout == '' ||logout.length < 1 || typeof logout != 'string'){
 		return '00:00';
 	}
	var login = login.split(':');
	var logout = logout.split(':');
	var inhour = parseInt(login[0]);
	var inminute = parseInt(login[1]);
	var outhour = parseInt(logout[0]);
	var outminute = parseInt(logout[1]);
	var totalloginminutes = inhour + inminute;
	// var totallogoutnminutes = outhour + outminute;
	var hour = ""+  outhour - inhour +" hours";
	var minutes = ""+  outminute - inminute + " minutes" ;
	return hour +' and '+minutes;
}