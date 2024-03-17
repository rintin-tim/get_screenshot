$(document).ready(function() {

    // open modal
    $("a.screenshot").click(function(e) {
        newUrl = e.target.dataset.modalSrc;
        console.log(e.target.dataset.modalSrc);
        window.modalImg = $('#modurl').attr('src', newUrl)[0]; // set the image url in the modal
        createSrcList();

        function createSrcList() {
            var imgs = $('img[data-screenshot]');
            var i;

            window.srcs = [];
            for (i = 0; i < imgs.length; i++) {
                srcs.push(imgs[i].dataset.modalSrc);
            };

            console.log(srcs);
            console.log(e)

        };

        populateOverview();

        function populateOverview() {
            // use modal src to match data attributes in thumb/result img tag
            console.log('populate executed')

            thumbImage = $('img[data-modal-src="' + window.modalImg.src + '"]')[0]
            console.log('thumb image: ' + thumbImage)

            platform = thumbImage.dataset.modalPlatform
            os = thumbImage.dataset.modalOs
            testUrl = thumbImage.dataset.modalTesturl

            $('#platform').text(platform); // set the platform in the modal
            $('#os').text(os); // set the os in the modal
            $('#testurl').text(testUrl); // set the os in the modal
        }
    })

    // click next/previous
    $('a#next, a#previous').click(function(e) {

            console.log('click event fired')
            targetId = e.target.id
            console.log('target id: ' + targetId)

            getNextPrevUrl(targetId)

            function getNextPrevUrl(targetId) {
                currentUrl = $('#modurl').attr('src'); // get current image url
                console.log('current url: ' + currentUrl)

                if (targetId == 'previous') {
                    urlIndex = srcs.indexOf(currentUrl) - 1;
                    console.log('previous index: ' + urlIndex)
                } else if (targetId == 'next') {
                    urlIndex = srcs.indexOf(currentUrl) + 1;
                    console.log('next index: ' + urlIndex)
                } else {
                    throw "target id not found"
                }

                nextPrevUrl = srcs[urlIndex]
                console.log('next / prev: ' + nextPrevUrl);
                $('#modurl').attr('src', nextPrevUrl); // get current image url
                $('div.jquery-modal.blocker.current').scrollTop(0);
            }
        }

    )

}) // end of docReady