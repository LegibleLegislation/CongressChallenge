
// vars

var vis = {
	billDataFile: 'data/topics_data_feb092018.json',
	billsData: [],
	sponsorDataFile: 'data/sponsor_parties_mar142018.json',
	sponsorData: []
}

// utils

vis.getBillByID = function(id) {
	var bill = vis.billsData.filter(function(d) { return d.bill_id_nice == id; })[0]
	// catch bill undefined ?
	return bill;
}

// var once = true
vis.getBillTags = function(bill) {
	var good = bill.topics.tags
		.filter(function(d) { return d.cosine < 0.3 && d.name.length < 30; })
		.map(d => d.name)
	// fallback if no good tags
	if (good.length == 0) good = [bill.policy_area]
	// if (once) console.log('getBillTags',bill, good); once = false
	return good
}

// https://gist.github.com/ralphcrisostomo/3141412
function compressArray(original) {
 
	var compressed = [];
	// make a copy of the input array
	var copy = original.slice(0);
 
	// first loop goes over every element
	for (var i = 0; i < original.length; i++) {
 
		var myCount = 0;	
		// loop over every element in the copy and see if it's the same
		for (var w = 0; w < copy.length; w++) {
			if (original[i] == copy[w]) {
				// increase amount of times duplicate is found
				myCount++;
				// sets item to undefined
				delete copy[w];
			}
		}
 
		if (myCount > 0) {
			var a = new Object();
			a.value = original[i];
			a.count = myCount;
			compressed.push(a);
		}
	}
 
	return compressed;
};


// draw

vis.drawChart = function(congress) {

	d3.selectAll('.party').remove()
	d3.select('.common').remove()

	d3.select('.main').append('div').attr('class', 'party Democrat')
	d3.select('.main').append('div').attr('class', 'common')
	d3.select('.main').append('div').attr('class', 'party Republican')

	// let parties = Object.keys(vis.sponsorData)
	let parties = ['Democrat', 'Republican']

	let allTags = [],
		demTags = [],
		indieTags = [],
		repubTags = []

	let fontScale = d3.scaleLinear()
		.range([11, 24])
		.domain([1, 26]) // hardcoded to 115th congress

	parties.forEach( party => {

		let partyDiv = d3.select('.party.' + party)

		partyDiv.append('div').attr('class', 'title').html(party)

		let theseBills = vis.billsData
			.filter(function(d, i) { return d.congress == congress && d.sponsor_party == party; })
		
		let partyTags = []
		theseBills.forEach((b,i) => {
			// let bill = vis.getBillByID(b)
			let bill = b
			// if (i < 1) console.log('bill',b)
			let tags = vis.getBillTags(bill)
			if (tags[0] == '') return 
			tags.forEach(t => {
				 partyTags.push(t)
			})
		})

		partyTags = _.sortBy(partyTags, d => d)

		let compressed = compressArray(partyTags).filter(d => d.value != null)

		compressed = _.sortBy(compressed, d => d.count).reverse()

		// store tags for later comparison
		var arr = demTags
		if (party == 'Independent') {
			arr = indieTags;
		} else if (party == 'Republican') {
			arr = repubTags;
		}

		compressed.forEach(d => {
			arr.push({
				party: party,
				value: d.value,
				count: d.count
			})
		})

		var tagDivs = partyDiv.append('div').attr('class', 'tags')
			.selectAll('.tag')
			.data(compressed)
			.enter().append('div')
			.attr('class', 'tag')
			.html(d => d.value)
			.style('font-size', d => fontScale(d.count) + 'px')
			.on('mouseover', showTooltip)
			.on('mouseout', hideTooltip)
		tagDivs.filter(d => d.count > 1)
				.append('div')
				.attr('class', 'badge')
				.html(d => d.count)

		// end parties forEach
	})

	// just Ds, Rs
	let commonTags = []

	demTags.forEach(d => {
		repubTags.forEach(r => {
			if (d.value == r.value) {
				commonTags.push({
					value: d.value,
					demCount: d.count,
					repubCount: r.count,
					totalCount: d.count + r.count,
					avgCount: (d.count + r.count) / 2
				})
			}
		})
	})

	commonTags = _.sortBy(commonTags, 'totalCount').reverse()

	let common = d3.select('.common');

	common.append('div').attr('class', 'title').html('Common')

	var tagDiv = common.append('div').attr('class', 'tags')
		.selectAll('.tag')
		.data(commonTags)
		.enter()
		.append('div').attr('class', 'tag common')
		.attr('style', 'background: none')

	tagDiv.append('div')
		.attrs({
			class: 'bg Demo'
		})
		.styles({
			width: d => Math.ceil(100 * d.demCount / d.totalCount) + '%'
		})

	tagDiv.append('div')
		.attrs({
			class: 'bg Repub' 
		})
		.styles({
			width: d => Math.floor(100 * d.repubCount / d.totalCount) + '%'
		})

	tagDiv.append('div').attr('class', 'tagCommonTxt')
		// .html(d => `${d.value} D:${d.demCount} R:${d.repubCount}`)
		.html(d => `${d.value} <div class="badge">${d.totalCount}</div>`)
		.style('font-size', d => fontScale(d.avgCount * 1) + 'px')



	function showTooltip(d) {
		// var txt = `${d.party} : ${d.count}`
		// d3.select('.tooltip').style('opacity', 1)
		// 	.html(txt)
	}

	function hideTooltip(d) {
		// d3.select('.tooltip').style('opacity', 0)
	}
}

// wrangle

vis.wrangleData = function(data) {
	var bills = data[0].bills

	var count = 0;
	for (var b in bills) {
		let bill = bills[b]
		bill.momentDate = moment(bill.status_at, 'YYYY-MM-DD')
		bill.niceDate = bill.momentDate.format('dddd, MMMM Do YYYY')
		bill.year = bill.status_at.substr(0, 4)
		bill.month = bill.status_at.substr(5, 2)
		// if (count++ < 2) console.table(bill)
		vis.billsData.push(bill)
	}

	var sponsors = data[1]

	vis.sponsorData = sponsors;

	console.log(vis.billsData[0])

	d3.select('#congressNum').on('change', () => {
		let val = d3.select('select').property('value')
		// console.log(val)
		vis.drawChart(val)
	})
	d3.select('body').on('mousemove', () => {
		var x = (d3.event.pageX - 100) + 'px',
			y = (d3.event.pageY + 10) + 'px'
		// console.log('tt: ' + x + ', ' + y)
		d3.select('.tooltip')
			.styles({
				top: y,
				left: x
			})
	})
	d3.select('.modal').on('click', () => d3.select('.modal').classed('hide', 'true'))

	d3.select('.item.about').on('click', ()=> {
		d3.select('.modal').classed('hide', false)
		d3.select('.modal .about').classed('hide', false)
		d3.select('.modal .video').classed('hide', true)
	})

	d3.select('.item.video').on('click', ()=> {
		d3.select('.modal').classed('hide', false)
		d3.select('.modal .about').classed('hide', true)
		d3.select('.modal .video').classed('hide', false)
	})

	vis.drawChart(115)
}

// load

vis.loadData = function() {
	d3.queue()
		.defer(d3.json, vis.billDataFile)
		// .defer(d3.json, vis.sponsorDataFile)
		.awaitAll( (err, results) => {
			if (err) throw err;
			vis.wrangleData(results)
		})
}

vis.loadData()