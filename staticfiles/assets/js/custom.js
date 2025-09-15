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
	
	
	document.documentElement.className="js";var supportsCssVars=function(){var e,t=document.createElement("style");return t.innerHTML="root: { --tmp-var: bold; }",document.head.appendChild(t),e=!!(window.CSS&&window.CSS.supports&&window.CSS.supports("font-weight","var(--tmp-var)")),t.parentNode.removeChild(t),e};supportsCssVars()||alert("Please view this demo in a modern browser that supports CSS Variables.");
	
	
	
	// scroll funtion
	
	
	(function() {
			function getRandomInt(min, max) {
				return Math.floor(Math.random() * (max - min + 1)) + min;
			}

			[].slice.call(document.querySelectorAll('.isolayer')).forEach(function(el) {
				new IsoGrid(el, {
					type : 'scrollable',
					transform : 'translateX(17vw) translateY(550px) rotateX(42deg) rotateZ(0deg)',
					stackItemsAnimation : {
						properties : function(pos) {
							return {
								translateZ: (pos+1) * 50,
								rotateZ: getRandomInt(-3, 3)
							};
						},
						options : function(pos, itemstotal) {
							return {
								type: dynamics.bezier,
								duration: 500,
								points: [{"x":0,"y":0,"cp":[{"x":0.2,"y":1}]},{"x":1,"y":1,"cp":[{"x":0.3,"y":1}]}],
								//delay: (itemstotal-pos-1)*40
							};
						}
					},
					onGridLoaded : function() {
						classie.add(document.body, 'grid-loaded');
					}
				});
			});
		})();



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
	
	
	
	
	var TxtType = function(el, toRotate, period) {
        this.toRotate = toRotate;
        this.el = el;
        this.loopNum = 0;
        this.period = parseInt(period, 10) || 2000;
        this.txt = '';
        this.tick();
        this.isDeleting = false;
    };

    TxtType.prototype.tick = function() {
        var i = this.loopNum % this.toRotate.length;
        var fullTxt = this.toRotate[i];

        if (this.isDeleting) {
        this.txt = fullTxt.substring(0, this.txt.length - 1);
        } else {
        this.txt = fullTxt.substring(0, this.txt.length + 1);
        }

        this.el.innerHTML = '<span class="wrap">'+this.txt+'</span>';

        var that = this;
        var delta = 200 - Math.random() * 100;

        if (this.isDeleting) { delta /= 2; }

        if (!this.isDeleting && this.txt === fullTxt) {
        delta = this.period;
        this.isDeleting = true;
        } else if (this.isDeleting && this.txt === '') {
        this.isDeleting = false;
        this.loopNum++;
        delta = 500;
        }

        setTimeout(function() {
        that.tick();
        }, delta);
    };


                  function write (obj, sentence, i, cb) {
                    if (i != sentence.length) {
                      setTimeout(function () {
                        i++
                        console.log('in timeout', i)
                        obj.innerHTML = sentence.substr(0, i+1) +' <em aria-hidden="true"></em>';
                        write(obj, sentence, i, cb)
                      }, 50)
                    } else {
                      console.log(i)
                      cb()
                    }
                  }
                   function erase (obj, cb,i) {
                   var sentence = obj.innerText
                      if (sentence.length != 0) {
                       setTimeout(function () {
                       sentence = sentence.substr(0,sentence.length-1)
                       console.log('in timeout', i)
                       obj.innerText = sentence
                       erase(obj, cb)
                        }, 18/(i*(i/10000000)))
                        } else {
                        obj.innerText = " "
                        cb()
                     }
                    }
                    var typeline = document.querySelector("#typeline")

                     function writeerase(obj, sentence, time, cb) {
                      write(obj, sentence, 0, function () {
                       setTimeout(function () {
                       erase(obj, cb) }, time) })
                       }

                  var sentences = [
                   "Badminton", "Baseball", "Basketball", "Cricket", "Football", "Hockey", "Racing", "Rugby", "Tennis", "wwe"
                  ]
                    
                  var counter = 0
                  function loop () {
                    var sentence = sentences[counter % sentences.length]
                    writeerase(typeline, sentence, 1500, loop)
                    counter++
                  }

                  loop()
				  
				  
	// land	  
				  
	$('.landing-item-inner').hover(function()
	{
		var $img = $(this).find('img'),
		imgHtoAnimate = $img.height() - $(this).height();
		$(this).find('img').stop().animate({marginTop: -(imgHtoAnimate)}, 5000);
	},
	function()
	{
		$(this).find('img').stop().animate({marginTop: 0},2500);
	});
	
 });

})(jQuery);	