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
	
	
	 /*--- Responsive Menu Start ----*/

$("#toggle").on("click", function(){
  var w = $('#sidebar').width();
  var pos = $('#sidebar').offset().left;
 
  if(pos == 0){
  $("#sidebar").animate({"left": -500}, "slow");
  }
  else
  {
  $("#sidebar").animate({"left": "0"}, "slow");
  }
  
});

$("#toggle_close").on("click", function(){
  var w = $('#sidebar').width();
  var pos = $('#sidebar').offset().left;
 
  if(pos == 0){
  $("#sidebar").animate({"left": -500}, "slow");
  }
  else
  {
  $("#sidebar").animate({"left": "0"}, "slow");
  }
  
});

(function($){
$(document).ready(function(){

$('#cssmenu li.active').addClass('open').children('ul').show();
	$('#cssmenu li.has-sub>a').on('click', function(){
		$(this).removeAttr('href');
		var element = $(this).parent('li');
		if (element.hasClass('open')) {
			element.removeClass('open');
			element.find('li').removeClass('open');
			element.find('ul').slideUp(200);
		}
		else {
			element.addClass('open');
			element.children('ul').slideDown(200);
			element.siblings('li').children('ul').slideUp(200);
			element.siblings('li').removeClass('open');
			element.siblings('li').find('li').removeClass('open');
			element.siblings('li').find('ul').slideUp(200);
		}
	});

});
})(jQuery);


function quick_search(){
	'use strict';
	/* Quik search in header on click function */
	var quikSearch = $("#quik-search-btn");
	var quikSearchRemove = $("#quik-search-remove");
	
	quikSearch.on('click',function() {
		$('.dez-quik-search').animate({'width': '100%' });
		$('.dez-quik-search').delay(500).css({'left': '0'  });
    });
    
	quikSearchRemove.on('click',function() {
        $('.dez-quik-search').animate({'width': '0%' ,  'right': '0'  });
		$('.dez-quik-search').css({'left': 'auto'  });
    });	
	/* Quik search in header on click function End*/
}
quick_search();

	
		$('.about_slider_wrapper .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:true,
				 smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="fa fa-angle-double-left" aria-hidden="true"></i>','<i class="fa fa-angle-double-right" aria-hidden="true"></i>'],
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
              });

	
				//----------- upcoming games slider js -------------//
	
	$(document).ready(function() {
              $('.upcoming_slider_wrapper .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 1,
                    nav: true
                  },
                  900: {
                    items: 2,
                    nav: true
                  },
                  1000: {
                    items: 3,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
							 
			//*********** vertical slider ***********//	 	
				$(".album-slider").bxSlider({
					minSlides: 1,
					maxSlides: 10,
					slideWidth: 350,
					ticker: true,
					tickerHover: true,
					speed: 20000,
					useCSS: false,
					pager:false,
					infiniteLoop: false
					
					});
			
			
				/*------------scroll bar-------------*/
				
			$("#tg-playerscrollbar").mCustomScrollbar({
				axis:"y",
			});
			

 //* Isotope js
 

    function protfolioIsotope(){
        if ( $('.protfolio_area, .portfolio_grid, .portfolio_gridIII').length ){ 
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
	
			//----------- testimonial slider js -------------//
			$(document).ready(function() {
            $('.testi_slider_wrapper .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
                autoplay: false,
                responsiveClass: true,
                smartSpeed: 1200,
                navText: ['<i class="flaticon-back"></i>', '<i class="flaticon-next"></i>'],
                responsive: {
                    0: {
                        items: 1,
                        nav: true
                    },
					500: {
                        items: 1,
                        nav: true
                    },
                    700: {
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
		
		
		//* slider *//
	 $(document).ready(function() {
            $('.cc_ps_top_slider_section .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
                autoplay: false,
                responsiveClass: true,
                smartSpeed: 1200,
                navText: ['<i class="fa fa-angle-double-left" aria-hidden="true"></i>', '<i class="fa fa-angle-double-right" aria-hidden="true"></i>'],
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
	
	
			//----------- trophy slider js -------------//
	
	$(document).ready(function() {
              $('.trophy_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  500: {
                    items: 1,
                    nav: true
                  },
                  700: {
                    items: 3,
                    nav: true
                  },
                  1000: {
                    items: 4,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
			
			//----------- trophy slider js -------------//
	
	$(document).ready(function() {
              $('.product_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  500: {
                    items: 2,
                    nav: true
                  },
                  700: {
                    items: 2,
                    nav: true
                  },
                  1000: {
                    items: 4,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
			
						
			//----------- trophy slider js -------------//
	
	$(document).ready(function() {
              $('.player_II_slider .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 2,
                    nav: true
                  },
                  900: {
                    items: 3,
                    nav: true
                  },
                  1000: {
                    items: 4,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
			
			
			
	//------ partner js ------------//
		$(document).ready(function() {
            $('.pn_slider_wraper .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
                autoplay: true,
                responsiveClass: true,
                smartSpeed: 1200,
               navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                    0: {
                        items: 2,
                        nav: true
                    },
					500: {
                        items: 2,
                        nav: true
                    },
                    700: {
                        items: 3,
                        nav: true
                    },
                    1000: {
                        items: 5,
                        nav: true,
                        loop: true,
                        margin: 20
                    }
                }
            })
        })
		
	
			
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

			//----------- upcoming games slider js -------------//
	
	$(document).ready(function() {
              $('.upcoming_slider_wrapper .owl-carousel').owlCarousel({
                loop: true,
                margin: 10,
				autoplay:false,
				smartSpeed: 1200,
                responsiveClass: true,
				navText : ['<i class="flaticon-back"></i>','<i class="flaticon-next"></i>'],
                responsive: {
                  0: {
                    items: 1,
                    nav: true
                  },
                  600: {
                    items: 1,
                    nav: true
                  },
                  900: {
                    items: 2,
                    nav: true
                  },
                  1000: {
                    items: 3,
                    nav: true,
                    loop: true,
                    margin: 20
                  }
                }
              })
            })
		
			
	$('#news_section_slider .owl-carousel').owlCarousel({
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
              });
			  

	
			// Contact Form Submition
	function checkRequire(formId , targetResp){
		targetResp.html('');
		var email = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/;
		var url = /(http|ftp|https):\/\/[\w-]+(\.[\w-]+)+([\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?/;
		var image = /\.(jpe?g|gif|png|PNG|JPE?G)$/;
		var mobile = /^[\s()+-]*([0-9][\s()+-]*){6,20}$/;
		var facebook = /^(https?:\/\/)?(www\.)?facebook.com\/[a-zA-Z0-9(\.\?)?]/;
		var twitter = /^(https?:\/\/)?(www\.)?twitter.com\/[a-zA-Z0-9(\.\?)?]/;
		var google_plus = /^(https?:\/\/)?(www\.)?plus.google.com\/[a-zA-Z0-9(\.\?)?]/;
		var check = 0;
		$('#er_msg').remove();
		var target = (typeof formId == 'object')? $(formId):$('#'+formId);
		target.find('input , textarea , select').each(function(){
			if($(this).hasClass('require')){
				if($(this).val().trim() == ''){
					check = 1;
					$(this).focus();
					targetResp.html('You missed out some fields.');
					$(this).addClass('error');
					return false;
				}else{
					$(this).removeClass('error');
				}
			}
			if($(this).val().trim() != ''){
				var valid = $(this).attr('data-valid');
				if(typeof valid != 'undefined'){
					if(!eval(valid).test($(this).val().trim())){
						$(this).addClass('error');
						$(this).focus();
						check = 1;
						targetResp.html($(this).attr('data-error'));
						return false;
					}else{
						$(this).removeClass('error');
					}
				}
			}
		});
		return check;
	}
	$(".submitForm").on("click", function() {
		var _this = $(this);
		var targetForm = _this.closest('form');
		var errroTarget = targetForm.find('.response');
		var check = checkRequire(targetForm , errroTarget);
		if(check == 0){
			var formDetail = new FormData(targetForm[0]);
			formDetail.append('form_type' , _this.attr('form-type'));
			$.ajax({
				method : 'post',
				url : 'ajax.php',
				data:formDetail,
				cache:false,
				contentType: false,
				processData: false
			}).done(function(resp){
				if(resp == 1){
					targetForm.find('input').val('');
					targetForm.find('textarea').val('');
					errroTarget.html('<p style="color:green;">Mail has been sent successfully.</p>');
				}else{
					errroTarget.html('<p style="color:red;">Something went wrong please try again latter.</p>');
				}
			});
		}
	});

		
 
 });

})(jQuery);	