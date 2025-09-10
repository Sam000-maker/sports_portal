
// toggle cross btn js
$(".toggle-main-wrapper , #toggle_close").on("click", function () {
  $("#sidebar").toggleClass("open")
});

$(document).ready(function () {
  $(".click-toggle").on('click', function () {
      $(".click-toggle").toggleClass("main");
  });
});
// number count for stats, using jQuery animate

// $('.counting').each(function() {
//   var $this = $(this),
//       countTo = $this.attr('data-count');
  
//   $({ countNum: $this.text()}).animate({
//     countNum: countTo
//   },

//   {

//     duration: 3000,
//     easing:'linear',
//     step: function() {
//       $this.text(Math.floor(this.countNum));
//     },
//     complete: function() {
//       $this.text(this.countNum);
//       //alert('finished');
//     }

//   });  
// });
// number count for stats, using jQuery animate

var deadline = 'august 31 2025 11:59:00 GMT-0400';
		function time_remaining(endtime){
			var t = Date.parse(endtime) - Date.parse(new Date());
			var seconds = Math.floor( (t/1000) % 60 );
			var minutes = Math.floor( (t/1000/60) % 60 );
			var hours = Math.floor( (t/(1000*60*60)) % 24 );
			var days = Math.floor( t/(1000*60*60*24) );
			return {'total':t, 'days':days, 'hours':hours, 'minutes':minutes, 'seconds':seconds};
		}
		function run_clock(id,endtime){
			var clock = document.getElementById(id);
			
			// get spans where our clock numbers are held
			var days_span = clock.querySelector('.days');
			var hours_span = clock.querySelector('.hours');
			var minutes_span = clock.querySelector('.minutes');
			var seconds_span = clock.querySelector('.seconds');

			function update_clock(){
				var t = time_remaining(endtime);
				
				// update the numbers in each part of the clock
				days_span.innerHTML = t.days;
				hours_span.innerHTML = ('0' + t.hours).slice(-2);
				minutes_span.innerHTML = ('0' + t.minutes).slice(-2);
				seconds_span.innerHTML = ('0' + t.seconds).slice(-2);
				
				if(t.total<=0){ clearInterval(timeinterval); }
			}
			update_clock();
			var timeinterval = setInterval(update_clock,1000);
		}
		run_clock('counter-stats',deadline);	

// golf-silder-box slider js start

$('.golf-silder-box .owl-carousel').owlCarousel({
  loop:false,
  margin:10,
  autoplay: false,
  nav: true,
  dots:false,
  navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>'],
  responsive:{
      0:{
          items:1
      },
      600:{
          items:1
      },
      1000:{
          items:1
      }
  }
})


// story slider js start

$('.stories-slider .owl-carousel').owlCarousel({
  loop:false,
  margin:10,
  autoplay: false,
  nav: false,
  dots:true,
  responsive:{
      0:{
          items:1
      },
      600:{
          items:1
      },
      1000:{
          items:1
      }
  }
})


		//-----------client slider js-------------//
    $('.client_slider .owl-carousel').owlCarousel({
      loop: true,
      margin: 20,
      autoplay:true,
      responsiveClass: true,
      navText : ['<i class="fa fa-angle-left" aria-hidden="true"></i>','<i class="fa fa-angle-right" aria-hidden="true"></i>'],
      responsive: {
        0: {
          items: 1,
          nav: false
        },
        600: {
          items: 4,
          nav: false
        },
        1000: {
          items: 6,
          nav: false,
          loop: true,
          margin: 20
        }
      }
    });



    // flip css start
    document.querySelector('.card').addEventListener('click', function() {
      this.classList.toggle('flipped');
    });


    // animation js start
    $(document).on("scroll", function () {
        var pageTop = $(document).scrollTop()
        var pageBottom = pageTop + $(window).height()
        var tags = $(".fadein")

        for (var i = 0; i < tags.length; i++) {
        var tag = tags[i]

        if ($(tag).offset().top < pageBottom) {
            $(tag).addClass("visible")
        } else {
            $(tag).removeClass("visible")
        }
        }
    })