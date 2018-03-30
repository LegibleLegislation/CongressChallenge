
// vars

var testData = {}


// setup Vue

var app = new Vue({
	el: '#app',
	data: {
		sponsorDataFile: 'data/sponsor_parties_mar142018.json',
		sponsorData: [],
		billDataFile: 'data/topics_data_feb092018.json',
		billsData: {},
		timelineData: [],
		policyDatafile: 'data/policy_areas_feb092018.json',
		policyData: [],
		currentBillID: null
	},
	methods: {
		init: function() {
			// console.log('init')
			this.loadBills()
		},
		loadBills: function() {
			d3.json(this.billDataFile, (error, data) => {
				if (error) throw error;
				console.log('loaded bills', data)
				this.timelineData = data.timeline;
				testData = data.bills;
				this.billsData = data.bills;
				// this.currentBillID = data.bills.keys(ahash)[0]
				// urgh hardcode
				this.currentBillID = 'hr1-115'
				// yeah there should be a smarter way to promsie-chain this stuff but...
				this.loadSponsors()
			})
		},
		loadSponsors: function() {
			d3.json(this.sponsorDataFile, (error, data) => {
				if (error) throw error;
				console.log('loaded sponsors', data)
				this.sponsorData = data;
				this.loadPolicies()
			})
		},
		loadPolicies: function() {
			d3.json(this.policyDatafile, (error, data) => {
				if (error) throw error;
				console.log('loaded policies', data)
				// this.policyData = data;
				// convert obj to arr
				for (var metaPolicy in data) {
					var area = this.policyData.push({ 
						name: metaPolicy, 
						type: 'metaPolicy', 
						children: []})
					for (var subPolicy in data[metaPolicy]) {
						this.policyData.filter(function(d) { return d.name == metaPolicy; })[0]
						.children.push({ 
							name: subPolicy, 
							type: 'subPolicy', 
							bills: data[metaPolicy][subPolicy].bills})
						// this.policyData[metaPolicy][subPolicy] = data[metaPolicy][subPolicy]
					}
				}
				// this.loadPolicies()
			})
		},
		getBill: function(billID) {
			console.log('getBill ' + billID)
			// return this.billsData[billID]
			this.currentBillID = billID;
		},
		formatDate: function(d) {
			var m = moment(d, 'YYYY-MM-DD')
			return m.format('dddd, MMMM Do YYYY')
		}

	},
	computed: {
		currentBill: function() {
			return this.billsData[this.currentBillID]
		},
		relevantTags: function() {
			var bill = this.billsData[this.currentBillID]
			// cosine cutoff: 
			// if  > 0.3 || bestname.length > 30 : 
				// fallback to CRO policy
			var good = bill.topics.tags.filter(function(d) { return d.cosine > 0.3 && d.name.length < 30; })
				.map(d => d.name)
			if (good.length == 0) good = [bill.policy_area]

			return good
		}
	},
	mounted: function() {
		this.init()
	}
	// end Vue app
});