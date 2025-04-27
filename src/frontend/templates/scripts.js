// selection counter
const selectionCounter = document.getElementById('selection-counter');

function updateSelectionCounter() {
      const selectedRegionDivs = regionList.querySelectorAll(`.region-entity.${classNameToToggle}`);
      const count = selectedRegionDivs.length;
      selectionCounter.innerHTML = '';
      for (let i = 0; i < count; i++) {
          const circle = document.createElement('span');
          circle.classList.add('counter-circle');
          selectionCounter.appendChild(circle);
      }
  }


// double region selection
const regionList = document.querySelector('.interaction__region-list');
const svgMap = document.getElementById('regions-map');
const classNameToToggle = 'selected_region';
const deprecated = ['donetsk_DEPR', 'luhansk_DEPR', 'crimea_DEPR'];
let isSelectionLocked = false;

function toggleRegionSelection(targetId) {
  if (isSelectionLocked) return;         

  // svg case
  const targetPath = svgMap.querySelector(`path[id="${targetId}"]`);
  targetPath.classList.toggle(classNameToToggle);

  // list case
  const targetSpan = regionList.querySelector(`.region-entity__name[id="${targetId}"]`);
  const targetRegionEntityDiv = targetSpan.closest('.region-entity');
  targetRegionEntityDiv.classList.toggle(classNameToToggle);

  updateSelectionCounter();
}

regionList.addEventListener('click', function(event) {
        const targetSpan = event.target.closest('.region-entity__name');
        if (targetSpan && targetSpan.id && !deprecated.includes(targetSpan.id)) {
            toggleRegionSelection(targetSpan.id);
        }
});

svgMap.addEventListener('click', function(event) {
        //  to handle clicks on potential inner elements of path too
        const targetPath = event.target.closest('path[id]');
        if (targetPath && targetPath.id && !deprecated.includes(targetPath.id)) {
            toggleRegionSelection(targetPath.id);
        }
});


// custom cursor
const customCursor = document.getElementById('custom-cursor');
let isOverTarget = false;

document.addEventListener('mousemove', function(event) {
    customCursor.style.left = `${event.clientX}px`;
    customCursor.style.top = `${event.clientY}px`;
  });

  // to check map as a hover target
  function isHoverTarget(element) {
      if (!element) return false;
      const pathTarget = element.closest('#regions-map path[id]');
      if (pathTarget) return true;

      return false;
  }

  document.addEventListener('mouseover', function(event) {
      if (isHoverTarget(event.target)) {
          if (!isOverTarget) { 
             customCursor.classList.add('rotate');
             isOverTarget = true;
          }
      }
  });

   document.addEventListener('mouseout', function(event) {
      // check if the new element is also a target
      if (isHoverTarget(event.target)) {
          if (!isHoverTarget(event.relatedTarget)) { 
              customCursor.classList.remove('rotate');
              isOverTarget = false;
          }
      }
  });

  // fallback
  document.addEventListener('mouseleave', function() {
      customCursor.classList.remove('rotate');
      isOverTarget = false;
  });

document.addEventListener('click', function() {
    customCursor.classList.add('pulsate');
    setTimeout(() => {
        customCursor.classList.remove('pulsate');
    }, 200);
});


// map tooltips
const tooltip = document.getElementById('region-tooltip');
let currentHoveredPathId = null; 

function getRegionNameById(id) {
  if (!id) return null;
  const regionSpan = document.querySelector(`.region-entity__name[id="${id}"]`);
  return regionSpan ? regionSpan.textContent : null;
}

function updateTooltipPosition(event) {
  const tooltipWidth = tooltip.offsetWidth;
  const tooltipHeight = tooltip.offsetHeight;
  const padding = 30; 

  let left = event.clientX + padding;
  let top = event.clientY + padding;

  // beyond width
  if (left + tooltipWidth > window.innerWidth) {
    left = event.clientX - tooltipWidth - padding;
  }

  // beyond height
  if (top + tooltipHeight > window.innerHeight) {
    top = event.clientY - tooltipHeight - padding;
  }

  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

// mouseover on svg 
svgMap.addEventListener('mouseover', function(event) {
    const targetPath = event.target.closest('path[id]');

    if (targetPath) {
        currentHoveredPathId = targetPath.id; 
        const regionName = getRegionNameById(currentHoveredPathId);

        if (regionName) {
            tooltip.textContent = regionName;
            tooltip.style.display = 'block'; 
            updateTooltipPosition(event);
        } else {
            tooltip.style.display = 'none'; // if no name found
        }
    }
});

// mousemove on svg
svgMap.addEventListener('mousemove', function(event) {
    // only if tooltip still over a path
    if (tooltip.style.display === 'block' && currentHoveredPathId) {
        // still over the original path or one of its children
        const stillOverPath = event.target.closest(`path[id="${currentHoveredPathId}"]`);
        if (stillOverPath) {
            updateTooltipPosition(event);
        } else {
            tooltip.style.display = 'none';
            currentHoveredPathId = null;
        }
    }
});

// mouseout from svg
svgMap.addEventListener('mouseout', function(event) {
    const targetPath = event.target.closest('path[id]');
    if (targetPath && targetPath.id === currentHoveredPathId) {
        tooltip.style.display = 'none';
        currentHoveredPathId = null;
    }
});






// select-all button
const allRegionIds = [
  "kyiv_city","kyiv","vinnytsia","lutsk","dnipro","zhytomyr",
  "uzhhorod","zaporizhzhia","ivano-frankivsk","kropyvnytskyi",
  "lviv","mykolaiv","odesa","poltava","rivne","sumy","ternopil",
  "kharkiv","kherson","khmelnytskyi","cherkasy","chernivtsi","chernihiv"
];

let allSelected = false;
const selectAllBtn = document.querySelector('.select-all-regions');
selectAllBtn.addEventListener('click', () => {
  allSelected = !allSelected;

  allRegionIds.forEach(id => {
    // svg path
    const path = svgMap.querySelector(`path[id="${id}"]`);
    if (path) {
      path.classList[ allSelected ? 'add' : 'remove' ](classNameToToggle);
    }

    // list items
    const span = regionList.querySelector(`.region-entity__name[id="${id}"]`);
    if (span) {
      const div = span.closest('.region-entity');
      div.classList[ allSelected ? 'add' : 'remove' ](classNameToToggle);
    }
  });

  updateSelectionCounter();

  selectAllBtn.textContent = allSelected
    ? 'DESELECT ALL'
    : 'SELECT ALL';
});

const supportElements = document.querySelectorAll(".region-entity__support");

const today = new Date();
const monthNames = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
const formattedDate = `${monthNames[today.getMonth()]} ${today.getDate()}`;

supportElements.forEach(el => {
    const parts = el.textContent.split(',');
    if (parts.length > 1) {
        el.textContent = parts[0].trim() + ', ' + formattedDate;
    } else {
        el.textContent = formattedDate;
    }
});



// fetch and show predictions for selecter regions
document.addEventListener('DOMContentLoaded', () => {
    const mainContainer = document.getElementById('main-container');
    const mapSvg = document.querySelector('.map');
    const interactionDiv = document.querySelector('.interaction');
    let fetchedForecasts = {};

    const actionAfterContainer = document.querySelector('.action-after'); // DELEGATION

    // fetch button
    const fetchBtn = document.querySelector('.fetch-forecast');
    async function fetchForecastData() {

        const apiToken = window.APP_CONFIG?.API_TOKEN; 
        if (!apiToken) {
            console.error("API Token not found");
            return;
        }

        const response = await fetch('/api/v1/alarm-forecast', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token: apiToken })
        });

        if (!response.ok) {
            let errorMsg = `HTTP error, status: ${response.status}`;
            try {
                const errorData = await response.json();  // 
                errorMsg = errorData.message || errorMsg;
            } catch (error) {
                console.error('Error object:', error);
                console.error('Error name:', error.name);
                console.error('Error message:', error.message);
            }
            return;
        }

        const data = await response.json();

      // store the relevant part of the data
      timeData = data.regions_forecast;

      // count how many selected
      const selectedEls = regionList.querySelectorAll('.region-entity.selected_region');
      if (selectedEls.length === 0) {
        return;
      }

      // lock further toggles
      isSelectionLocked = true;

      // mark the list
      document.querySelector('.interaction__form').classList.add('region-action');
      // svgMap.classList.add('region-action');

      // forecast cards building
      const container = document.querySelector('.action-after');
      container.innerHTML = '';   

      selectedEls.forEach(regionDiv => {
        const nameSpan = regionDiv.querySelector('.region-entity__name');
        const regionId   = nameSpan.id;
        const regionName = nameSpan.textContent;

        const card = document.createElement('div');
        card.className = 'region-entity_after';

        const info = document.createElement('div');
        info.className = 'region-entity__info';

        const spanName = document.createElement('span');
        spanName.id = regionId;
        spanName.className = 'region-entity__name';
        spanName.textContent = regionName + ',';

        const spanSupport = document.createElement('span');
        spanSupport.className = 'region-entity__support';
        spanSupport.textContent = 'Forecast';

        info.append(spanName, spanSupport);
        card.appendChild(info);

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'moreinfo');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('viewBox', '0 0 45 44');
        svg.setAttribute('height', '43');
        svg.setAttribute('width', '44');
        svg.innerHTML = `
          <path d="M3 41.5H43.5" stroke="#1A1A1A" stroke-width="3"/>
          <path d="M42 3L42 43" stroke="#1A1A1A" stroke-width="3"/>
          <path d="M42 41.5L2 2" stroke="#1A1A1A" stroke-width="3"/>
        `;
        card.appendChild(svg);

        container.appendChild(card);
      })};

    fetchBtn.addEventListener('click', fetchForecastData);

    function highlightRegion(regionId, activeColor = '#1a1a1a', inactiveColor = '#cbcbcb') {
        mapSvg.querySelectorAll('path').forEach(path => {
            if (path.id === regionId) {
                path.style.fill = activeColor;      
            } else {
                path.style.fill = inactiveColor;    
            }
        });
    }

    function resetToGlobalView() {
        const existingDetailedInfo = document.querySelector('.region-detailed-info');
        if (existingDetailedInfo) {
            existingDetailedInfo.remove();
        }

        if (mapSvg) {
            const classesToRemove = [];
            mapSvg.classList.forEach(className => {
                if (className.startsWith('map-transform-')) {
                    classesToRemove.push(className);
                }
            });
            mapSvg.classList.remove(...classesToRemove);

            mapSvg.querySelectorAll('path').forEach(p => p.style.fill = '');
        }

        if (interactionDiv) {
            interactionDiv.classList.remove('interaction-hidden');
        }

    }

    // region card
    actionAfterContainer.addEventListener('click', function(event) {
      const clickedRegionBlock = event.target.closest('.region-entity_after');

      if (!clickedRegionBlock) {
          return;
      }

      const regionSpan = clickedRegionBlock.querySelector('.region-entity__name[id]');
      const regionId = regionSpan.id;
      const regionName = regionSpan.textContent || regionSpan.innerText;

      // reset previous state
      resetToGlobalView();

      // add specific map-transform
      mapSvg.classList.add(`map-transform-${regionId}`);

      // add interaction-hidden
      interactionDiv.classList.add('interaction-hidden');

      // second info list
      const detailedInfoHTML = `
              <div class="region-detailed-info">
                  <div class="separator">
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="194" viewBox="0 0 10 194" fill="none">
                          <path d="M5.19141 10.0098C7.73152 10.0098 9.79068 7.95062 9.79069 5.41052C9.79069 2.87042 7.73152 0.811245 5.19141 0.811245C2.65131 0.811245 0.592144 2.87042 0.592144 5.41052C0.592144 7.95062 2.65131 10.0098 5.19141 10.0098ZM5.19141 193.406L6.05377 193.406L6.05378 5.41052L5.19141 5.41052L4.32905 5.41052L4.32904 193.406L5.19141 193.406Z" fill="#0A0A0B"></path>
                      </svg>
                  </div>
                  <div class="region-forecast">
                      <div class="region-forecast__info">
                          <span class="forecast-helper">ESTIMATED ALARM FORECAST FOR:</span>
                          <div class="forecast-id">
                              <div class="region-entity__info">
                                  <span id="${regionId}-display" class="region-entity__name">${regionName}</span>
                                  <span class="region-entity__type"></span>
                              </div>
                              <span class="region-entity__support">Apr. 2</span>
                          </div>
                      </div>
                      <div class="region-forecast__slider">
                          <div class="time-slider-container" id="${regionId}--details">
                              <svg viewBox="0 0 562 145" class="arc-svg">
                                  <path id="arc-path-${regionId}" d="M 5.11987 140.525 C 49.6373 57.9911 156.468 0 281 0 C 405.532 0 512.363 57.9911 556.88 140.525" stroke="#1A1A1A" stroke-width="2" fill="none"></path>
                              </svg>
                              <div class="handle"></div>
                              <div class="labels">
                                  <span class="label-start">00:00</span>
                                  <span class="label-end">23:00</span>
                              </div>
                          </div>
                      </div>
                      <div class="region-forecast__stats">
                          <div>
                              <div class="output">
                                  <span id="alarm_probability">----</span>
                              </div>
                              <div class="output">
                                  AT <span id="alarm_time_target">--:--</span>
                              </div>
                          </div>
                          <div class="region-return-to-list">WANNA RETURN TO A GLOBAL VIEW?</div>
                      </div>
                  </div>
              </div>`;

      mainContainer.insertAdjacentHTML('beforeend', detailedInfoHTML);
      highlightRegion(regionId);

      const newSliderContainer = document.getElementById(`${regionId}--details`);
      initializeSlider(newSliderContainer);

      const supportElements = document.querySelectorAll(".region-entity__support");

      const today = new Date();
      const monthNames = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
      const formattedDate = `${monthNames[today.getMonth()]} ${today.getDate()}`;

      supportElements.forEach(el => {
        const parts = el.textContent.split(',');
        if (parts.length > 1) {
          el.textContent = parts[0].trim() + ', ' + formattedDate;
        } else {
          el.textContent = formattedDate;
        }
      });

    });

    
    mainContainer.addEventListener('click', function(event) {
            if (event.target.matches('.region-return-to-list')) {
                resetToGlobalView();
            }
    });

});


// alarm slider for region cards
function initializeSlider(container) {
    const regionId = container.id; 
    const cleanRegionId = regionId.replace('--details', '');
    const regionDataKey = cleanRegionId
    .split('_') // to handle kyiv_city 
    .map(word => word.replace(/(?:^|-)(.)/g, (match, char) => match.toUpperCase())) // to handle ivano-frankivsk and keep hyphen
    .join(' ');

    const handle = container.querySelector('.handle');
    const arcPath = container.querySelector('path'); 
    const svg = container.querySelector('.arc-svg');

    // elements are unique within the current .region-detailed-info
    const alarmTimeTarget = document.getElementById(`alarm_time_target`);
    const alarmProbabilityTarget = document.getElementById(`alarm_probability`);

    if (!handle || !arcPath || !svg || !alarmTimeTarget || !alarmProbabilityTarget) {
       console.log({ container, handle, arcPath, svg, alarmTimeTarget, alarmProbabilityTarget });
       return;
    }
    if (typeof timeData === 'undefined' || !timeData || !timeData[regionDataKey]) {
        console.warn(`missing for ${regionDataKey}`);
    }

    let isDragging = false;
    let currentHour = 12; 
    const pathLength = arcPath.getTotalLength();
    const svgPoint = svg.createSVGPoint();
    let svgInverseCTM = null; 

    // path boundaries
    const pathStartX = 5.11987;
    const pathEndX = 556.88;
    const pathWidth = pathEndX - pathStartX;

    function updateSlider(hour) {
        hour = Math.max(0, Math.min(23, Math.round(hour))); 

        const isInitialUpdate = alarmTimeTarget.textContent === '--:--';
        if (!isInitialUpdate && hour === currentHour) {
            return;
        }

        currentHour = hour;

        const pos = arcPath.getPointAtLength((hour / 23) * pathLength);
        handle.style.transform = `translate(${pos.x}px, ${pos.y}px) translate(-50%, -50%)`;


        const formattedTime = `${String(hour).padStart(2, '0')}:00`;
        alarmTimeTarget.textContent = formattedTime;

        const probability = timeData?.[regionDataKey]?.[formattedTime];
        if (probability === true) {
            alarmProbabilityTarget.textContent = "High";
        } else if (probability === false) {
            alarmProbabilityTarget.textContent = "Low";
        } else {
            alarmProbabilityTarget.textContent = "NA";
        }
    }

    function getInverseCTM() {
        const ctm = svg.getScreenCTM();
        return ctm.inverse();
    }


    function onMouseMove(e) {
        if (!isDragging || !svgInverseCTM) return;

        svgPoint.x = e.clientX;
        svgPoint.y = e.clientY;

        let svgCoord;
        svgCoord = svgPoint.matrixTransform(svgInverseCTM);

        const clampedX = Math.max(pathStartX, Math.min(pathEndX, svgCoord.x));
        const estimatedHour = ((clampedX - pathStartX) / pathWidth) * 23;

        updateSlider(estimatedHour);
        e.preventDefault(); 
    }

    function onMouseUp() {
        if (isDragging) {
            isDragging = false;
            document.removeEventListener('mousemove', onMouseMove, true);
            document.removeEventListener('mouseup', onMouseUp, true);
        }
    }

    // listeners for THIS slider instance 
    handle.style.pointerEvents = 'auto'; 

    handle.addEventListener('mousedown', e => {
        svgInverseCTM = getInverseCTM();

        isDragging = true;
        document.addEventListener('mousemove', onMouseMove, true);
        document.addEventListener('mouseup', onMouseUp, true);
        e.preventDefault();
        e.stopPropagation(); 
    });

    container.addEventListener('wheel', e => {
        e.preventDefault(); 
        updateSlider(currentHour + (e.deltaY < 0 ? -1 : 1)); // by 1 hour based on scroll direction
    }, { passive: false }); 

    updateSlider(12); 
}