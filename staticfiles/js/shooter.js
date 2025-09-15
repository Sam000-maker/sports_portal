// Preloader 
jQuery(window).on('load', function () {
    jQuery("#status").fadeOut();
    jQuery("#preloader").delay(350).fadeOut("slow");
});


// menu dropdwon js start 

$(document).ready(function(){
    // $(".sub-menu").hide();
    $('.sub-btn1').click(function(){
        // $(".sub-menu").hide();
        $(this).next('.sub-menu1').slideToggle();
        $(this).find('.dropdwon').toggleClass('rotate');
    });
});
// menu dropdwon js end

// menu fixed js start
$(window).scroll(function () {
    var window_top = $(window).scrollTop() + 1;
    if (window_top > 100) {
        $('.menu-item-wrapper2').addClass('menu-fixed animated fadeInDown');
    } else {
        $('.menu-item-wrapper2').removeClass('menu-fixed animated fadeInDown');
    }
});

// menu fixed js end


// mobile responsive js start 
$(document).ready(function(){
    $('.sub-btn').click(function(){
        $(this).next('.sub-menu').slideToggle();
        $(this).find('.dropdown').toggleClass('rotate');
    });

    $('.menu-btn').click(function(){
        $('.side-bar').addClass('active');
        $('.menu-btn').css("visibility", "hidden");
    });

    $('.close-btn').click(function(){
        $('.side-bar').removeClass('active');
        $('.menu-btn').css("visibility", "visible");
    });
});
// mobile responsive js end

// banner js start 
$('.banner_slider_main_box .owl-carousel').owlCarousel({
    loop: true,
    margin: 10,
    nav: false,
    dots: false,
    autoplay: true,
    autoplayTimeout: 2000,

    responsive: {
        0: {
            items: 1
        },
        600: {
            items: 1
        },
        1000: {
            items: 1
        }
    }
})

// banner js end 




//   patner js start 
$('.partner_slider .owl-carousel').owlCarousel({
    loop: true,
    margin: 30,
    nav: false,
    dots: false,
    autoplay: true,
    autoplayTimeout: 1000,
    responsive: {
        0: {
            items: 1
        },
        600: {
            items: 3
        },
        1000: {
            items: 5
        }
    }
})

//   patner js end

// testimonail sec start
$(document).ready(function () {
$('.testimonail_slider_sec .owl-carousel').owlCarousel({
    loop: true,
    margin: 30,
    nav: true,
    dots: false,
    responsive: {
        0: {
            items: 1
        },
        767: {
            items: 2
        },
        1500: {
            items: 3
        }
    }
})
$(".testimonail_slider_sec .owl-prev").html('<svg viewBox="0 0 448 512"><path d="M9.4 233.4c-12.5 12.5-12.5 32.8 0 45.3l160 160c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L109.2 288H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H109.3l105.3-105.4c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0l-160 160z"/></svg>');
$(".testimonail_slider_sec .owl-next").html('<svg viewBox="0 0 448 512"><path d="M438.6 278.6c12.5-12.5 12.5-32.8 0-45.3l-160-160c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L338.8 224H32c-17.7 0-32 14.3-32 32s14.3 32 32 32h306.7L233.4 393.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0l160-160z"/></svg>');
});
// testimonail sec end


(function () {
    const second = 1000,
          minute = second * 60,
          hour = minute * 60,
          day = hour * 24;
  
    //I'm adding this section so I don't have to keep updating this pen every year :-)
    //remove this if you don't need it
    let today = new Date(),
        dd = String(today.getDate()).padStart(2, "0"),
        mm = String(today.getMonth() + 1).padStart(2, "0"),
        yyyy = today.getFullYear(),
        nextYear = yyyy + 1,
        dayMonth = "09/30/",
        birthday = dayMonth + yyyy;
    
    today = mm + "/" + dd + "/" + yyyy;
    if (today > birthday) {
      birthday = dayMonth + nextYear;
    }
    //end
    
    const countDown = new Date(birthday).getTime(),
        x = setInterval(function() {    
  
          const now = new Date().getTime(),
                distance = countDown - now;
  
          document.getElementById("days").innerText = Math.floor(distance / (day)),
            document.getElementById("hours").innerText = Math.floor((distance % (day)) / (hour)),
            document.getElementById("minutes").innerText = Math.floor((distance % (hour)) / (minute)),
            document.getElementById("seconds").innerText = Math.floor((distance % (minute)) / second);
  
          //do something later when date is reached
          if (distance < 0) {
            document.getElementById("headline").innerText = "It's my birthday!";
            document.getElementById("countdown").style.display = "none";
            document.getElementById("content").style.display = "block";
            clearInterval(x);
          }
          //seconds
        }, 0)
    }());

    $("#tg-playerscrollbar").mCustomScrollbar({
        axis:"y",
    });



    $(document).ready(function() {
        $('.youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
            // disableOn: 700,
            type: 'iframe',
            mainClass: 'mfp-fade',
            removalDelay: 160,
            preloader: false,
    
            fixedContentPos: false
        });
    });
    

    		// Magnific popup-video

	// $('.test-popup-link').magnificPopup({ 
    //     type: 'iframe',
    //     iframe: {
    //         markup: '<div class="mfp-iframe-scaler">'+
    //             '<div class="mfp-close"></div>'+
    //             '<iframe class="mfp-iframe" frameborder="0" allowfullscreen></iframe>'+
    //             '<div class="mfp-title">Some caption</div>'+
    //             '</div>',
    //         patterns: {
    //             youtube: {
    //                 index: 'youtube.com/', 
    //                 id: 'v=',
    //                 src: 'https://www.youtube.com/embed/ryzOXAO0Ss0'
    //             }
    //         }
    //     }
        // other options
    // });
    


  

// gallery js start

$('.portfolio_img_text').magnificPopup({
    delegate: '.img-link',
    type: 'image',
    tLoading: 'Loading image #%curr%...',
    mainClass: 'mfp-img-mobile',
    gallery: {
        enabled: true,
        navigateByImgClick: true,
        preload: [0, 1]
    },
    image: {
        tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
        titleSrc: function (item) {
            return item.el.attr('title') + '<small></small>';
        }
    }
});
$('.portfolio_img_icon').magnificPopup({
    delegate: '.img-link',
    type: 'image',
    tLoading: 'Loading image #%curr%...',
    mainClass: 'mfp-img-mobile',
    gallery: {
        enabled: true,
        navigateByImgClick: true,
        preload: [0, 1]
    },
    image: {
        tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
        titleSrc: function (item) {
            return item.el.attr('title') + '<small></small>';
        }
    }
});
// gallery js end



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



// header search bar js start
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
// header search bar  js  end


// mobile header search bar js start
function mobile_search(){
	'use strict';
	/* Quik search in header on click function */
	var quikSearch = $("#mobile-search-btn");
	var quikSearchRemove = $("#mobile-search-remove");
	
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
mobile_search();
// mobile header search bar js end
