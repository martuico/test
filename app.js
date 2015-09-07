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
		$scope.currentTime = (now.getHours() > 12) ?  (now.getHours() - 12).pad() + ':' + now.getMinutes()
							: now.getHours().pad() + ':' + now.getMinutes();
	  	$scope.add = function(){
	  		$scope.datas.push({login: $scope.currentTime,logout:''});
		}

		$scope.store = function(data){
			console.log(data);
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