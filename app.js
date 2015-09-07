(function(){
'use strict';

angular.module('myApp', [
	'ngRoute'
	])
	.config(function($routeProvider){
		$routeProvider
		  .when('/', {
		    templateUrl: 'index.html',
		    controller: 'MainCtrl'
		  })
	})
	.controller('loginController', function($scope) {
		$scope.datas = [];
		var now = new Date();
		$scope.datenow = now.getMonth().pad() +'/' + now.getDay().pad() + '/' + now.getFullYear();
		$scope.currentTime = now.getHours().pad() + ':' + now.getMinutes().pad();
		$scope.datas.push({login: $scope.currentTime,logout:'',totaltime:''});

		$scope.totalhours = function(){
			// $('.totaltime').each(function(){

			// });
		}

	  	$scope.add = function(){
	  		$scope.datas.push({login: $scope.currentTime,logout:'',totaltime:''});
		}
		$scope.store = function(data,index){
			var totaltime = tolalHours(data.login,data.logout);
			$scope.datas[index].totaltime = totaltime;
			var values = $scope.datas;
			var minutes = [];
			var hours = [];
			angular.forEach(values, function(value, key){
			  var re = value.totaltime.replace(' hours','').replace(' and ',':').replace(' minutes','').replace(' ','');

			 	re = re.split(':');
			 	minutes.push(re[1]);
			 	hours.push(re[0]);
			});

			if((parseInt(minutes.sum()) / 60) > 0){
				hours.push(parseInt(minutes.sum()) / 60);
			}

			$scope.totalhours = hours.sum();
		}

		$scope.remove = function(data,index){
			$scope.datas.splice(index, 1);
		}
	})
	.directive('clock', function(){
		return {
			restrict : 'AE',
			templateUrl: 'clock.html'
		}
	});
})();