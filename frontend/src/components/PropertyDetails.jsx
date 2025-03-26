import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  MapIcon,
  DocumentTextIcon,
  CurrencyDollarIcon,
  HomeIcon,
  UserIcon
} from '@heroicons/react/24/outline';

function PropertyDetails() {
  const { id } = useParams();
  
  // Fetch property details
  const { data: property, isLoading } = useQuery(
    ['property', id],
    () => fetch(`/api/property/${id}`).then(res => res.json())
  );
  
  // Fetch suggestions
  const { data: suggestions } = useQuery(
    ['suggestions', id],
    () => fetch(`/api/property/${id}/suggestions`).then(res => res.json())
  );
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {property.basics.address}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300">
          {property.basics.type} • Built {property.basics.year_built}
        </p>
      </motion.div>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <QuickStat
          icon={<HomeIcon />}
          label="Property Details"
          value={`${property.details.beds} beds • ${property.details.baths} baths`}
          subvalue={`${property.details.size} total`}
        />
        <QuickStat
          icon={<CurrencyDollarIcon />}
          label="Value"
          value={property.value.total}
          subvalue="Last assessed"
        />
        <QuickStat
          icon={<UserIcon />}
          label="Owner"
          value={property.owner.name}
          subvalue={`Since ${property.owner.since}`}
        />
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column - Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Property Information */}
          <Section title="Property Information">
            <div className="grid grid-cols-2 gap-4">
              <InfoItem label="Type" value={property.basics.type} />
              <InfoItem label="Year Built" value={property.basics.year_built} />
              <InfoItem label="Square Feet" value={property.details.size} />
              <InfoItem label="Lot Size" value={property.details.lot} />
              <InfoItem label="Bedrooms" value={property.details.beds} />
              <InfoItem label="Bathrooms" value={property.details.baths} />
              <InfoItem label="Zone" value={property.location.zone} />
              <InfoItem label="Flood Zone" value={property.location.flood_zone} />
            </div>
          </Section>
          
          {/* Value History */}
          <Section title="Value History">
            <div className="h-64">
              {/* Value history chart would go here */}
            </div>
          </Section>
          
          {/* Map */}
          <Section title="Location">
            <div className="h-96 bg-gray-100 rounded-lg">
              {/* Map would go here */}
            </div>
          </Section>
        </div>
        
        {/* Right Column - Insights & Actions */}
        <div className="space-y-8">
          {/* Smart Insights */}
          <Section title="Insights">
            {suggestions?.insights.map((insight, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start space-x-3 p-4 bg-white rounded-lg shadow-sm"
              >
                <span className="text-2xl">{insight.icon}</span>
                <p className="text-sm text-gray-600">{insight.text}</p>
              </motion.div>
            ))}
          </Section>
          
          {/* Quick Actions */}
          <Section title="Quick Actions">
            <div className="space-y-2">
              <ActionButton
                icon={<MapIcon />}
                label="View on Map"
                onClick={() => {}}
              />
              <ActionButton
                icon={<DocumentTextIcon />}
                label="Generate Report"
                onClick={() => {}}
              />
              <ActionButton
                icon={<ChartBarIcon />}
                label="Analyze Potential"
                onClick={() => {}}
              />
            </div>
          </Section>
          
          {/* Similar Properties */}
          <Section title="Similar Properties">
            {suggestions?.similar_properties.map((prop, i) => (
              <motion.div
                key={prop.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-4 bg-white rounded-lg shadow-sm"
              >
                <h4 className="font-medium">{prop.address}</h4>
                <p className="text-sm text-gray-600">{prop.preview.value}</p>
              </motion.div>
            ))}
          </Section>
        </div>
      </div>
    </div>
  );
}

// Helper Components
function Section({ title, children }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
        {title}
      </h3>
      {children}
    </div>
  );
}

function QuickStat({ icon, label, value, subvalue }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6"
    >
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
          <p className="text-xl font-semibold text-gray-900 dark:text-white">
            {value}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{subvalue}</p>
        </div>
      </div>
    </motion.div>
  );
}

function InfoItem({ label, value }) {
  return (
    <div>
      <dt className="text-sm text-gray-600 dark:text-gray-400">{label}</dt>
      <dd className="text-lg text-gray-900 dark:text-white">{value}</dd>
    </div>
  );
}

function ActionButton({ icon, label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center space-x-2 p-3 text-left text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
    >
      <span className="p-1 bg-gray-100 dark:bg-gray-600 rounded">
        {icon}
      </span>
      <span>{label}</span>
    </button>
  );
}

export default PropertyDetails;
