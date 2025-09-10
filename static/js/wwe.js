(function($) {
    "use strict";

    var tpj = jQuery;
    var revapi24;
	
	
  // Preloader 
    jQuery(window).on('load', function() {
        jQuery("#status").fadeOut();
        jQuery("#preloader").delay(350).fadeOut("slow");
    });
	
	
	 // on ready function
    jQuery(document).ready(function($) {
 
	
			// slider js //

        (function($) {

            //Function to animate slider captions 
            function doAnimations(elems) {
                //Cache the animationend event in a variable
                var animEndEv = 'webkitAnimationEnd animationend';

                elems.each(function() {
                    var $this = $(this),
                        $animationType = $this.data('animation');
                    $this.addClass($animationType).one(animEndEv, function() {
                        $this.removeClass($animationType);
                    });
                });
            }

            //Variables on page load 
            var $myCarousel = $('#carousel-example-generic'),
                $firstAnimatingElems = $myCarousel.find('.carousel-item:first').find("[data-animation ^= 'animated']");

            //Initialize carousel 
            $myCarousel.carousel();

            //Animate captions in first slide on page load 
            doAnimations($firstAnimatingElems);

            //Pause carousel  
            $myCarousel.carousel('pause');


            //Other slides to be animated on carousel slide event 
            $myCarousel.on('click slide.bs.carousel', function(e) {
                var $animatingElems = $(e.relatedTarget).find("[data-animation ^= 'animated']");
                doAnimations($animatingElems);
            });


        })(jQuery);
 
 
		//**** select2 js ****//
	
		$(".myselect").select2();
	
		
			//show hide login form js
			$('#menu_toggle_icon').on("click", function(e) {
				$('#menu_open').slideToggle();
				e.stopPropagation(); 
			});

			$(document).on("click", function(e){
				if(!(e.target.closest('#menu_open'))){	
					$("#menu_open").slideUp();   		
				}
		   });
		   
		   $(".rotate").on("click", function () {
			$(this).toggleClass("down");
		})
			
			

		/* upcoming_matches_slider js */
	
	$(document).ready(function() {
              $('.upcoming_matches_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="fa fa-angle-left" aria-hidden="true"></i>','<i class="fa fa-angle-right" aria-hidden="true"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 1,
                    nav: true
                  },
                  1000: {
                    items: 1,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
			
				

		//**-------   vedio wrapper js -------**//
						
	var video = document.getElementById("myVideo");
	var btn = document.getElementById("play-trigger");

	function myFunction() {
	  if (video.paused) {
		video.play();
		btn.innerHTML = "Pause";
	  } else {
		video.pause();
		btn.innerHTML = "Play";
	  }
	}

			// Magnific popup-video

	$('.test-popup-link').magnificPopup({ 
    type: 'iframe',
    iframe: {
        markup: '<div class="mfp-iframe-scaler">'+
            '<div class="mfp-close"></div>'+
            '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>'+
            '<div class="mfp-title">Some caption</div>'+
            '</div>',
        patterns: {
            youtube: {
                index: 'youtube.com/', 
                id: 'v=',
                src: 'https://www.youtube.com/embed/ryzOXAO0Ss0'
            }
        }
    }
    // other options
});

		

		//-----------client slider js-------------//
	$('.client_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:true,
                responsiveClass: true,
				navText : ['<i class="fa fa-angle-left" aria-hidden="true"></i>','<i class="fa fa-angle-right" aria-hidden="true"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 4,
                    nav: true
                  },
                  1000: {
                    items: 6,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              });

			

 //* Isotope js
    function protfolioIsotope(){
        if ( $('.protfolio_area, .portfolio_grid').length ){ 
            // Activate isotope in container
            $(".protfoli_inner, .portfoli_inner").imagesLoaded( function() {
                $(".protfoli_inner, .portfoli_inner").isotope({
                    layoutMode: 'masonry',  
                }); 
            });  
            
            // Add isotope click function 
            $(".protfoli_filter li").on('click',function(){
                $(".protfoli_filter li").removeClass("active");
                $(this).addClass("active"); 
                var selector = $(this).attr("data-filter");
                $(".protfoli_inner, .portfoli_inner").isotope({
                    filter: selector,
                    animationOptions: {
                        duration: 450,
                        easing: "linear",
                        queue: false,
                    }
                });
                return false;
            });  
        };
    }; 
 protfolioIsotope (); 

 
 
		/* upcoming_matches_slider js */
	
	$(document).ready(function() {
              $('.upcoming_matches_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="fa fa-angle-left" aria-hidden="true"></i>','<i class="fa fa-angle-right" aria-hidden="true"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 1,
                    nav: true
                  },
                  1000: {
                    items: 1,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
			
 
			 //------------ counter-section------------// 

    $('.counter_section').on('inview', function(event, visible, visiblePartX, visiblePartY) {
        if (visible) {
            $(this).find('.timer').each(function () {
                var $this = $(this);
                $({ Counter: 0 }).animate({ Counter: $this.text() }, {
                    duration: 2000,
                    easing: 'swing',
                    step: function () {
                        $this.text(Math.ceil(this.Counter));
                    }
                });
            });
            $(this).off('inview');
        }
    });
				
			
        // ===== Scroll to Top ==== 
        $(window).scroll(function() {
            if ($(this).scrollTop() >= 100) {
                $('#return-to-top').fadeIn(200);
            } else {
                $('#return-to-top').fadeOut(200);
            }
        });
        $('#return-to-top').on('click', function() {
            $('body,html').animate({
                scrollTop: 0
            }, 500);
        });
		
		
	
	

 });

})(jQuery);	