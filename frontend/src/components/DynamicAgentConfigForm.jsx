import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import logger from '../services/logger';

/**
 * Dynamic Agent Configuration Form Component
 * 
 * Generates a dynamic form from JSON Schema to configure agent parameters at runtime.
 * Supports type validation, constraints, and real-time updates.
 */
const DynamicAgentConfigForm = ({ agentId, onSuccess, onError }) => {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }, setValue } = useForm();

  useEffect(() => {
    fetchAgentSchema();
  }, [agentId]);

  const fetchAgentSchema = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/agents/${agentId}/schema`);
      
      if (response.data.success) {
        const schemaData = response.data.data.schema;
        setSchema(schemaData);
        
        // Set default values
        if (schemaData.properties) {
          Object.entries(schemaData.properties).forEach(([key, prop]) => {
            if (prop.default !== undefined) {
              setValue(key, prop.default);
            }
          });
        }
      }
    } catch (error) {
      logger.error('Failed to fetch agent schema', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data) => {
    try {
      setSubmitting(true);
      
      const response = await api.post(`/api/v1/agents/${agentId}/config`, {
        config: data
      });
      
      if (response.data.success) {
        logger.info('Agent configuration updated successfully', { agentId, config: data });
        if (onSuccess) {
          onSuccess(response.data.data);
        }
      }
    } catch (error) {
      logger.error('Failed to update agent configuration', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const renderField = (key, property) => {
    const fieldId = `config-${key}`;
    const required = schema.required?.includes(key);
    
    // Common input props
    const commonProps = {
      id: fieldId,
      ...register(key, {
        required: required ? `${property.title || key} is required` : false,
        min: property.minimum,
        max: property.maximum,
      }),
      disabled: submitting,
      className: "w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
    };

    switch (property.type) {
      case 'integer':
      case 'number':
        return (
          <input
            type="number"
            {...commonProps}
            step={property.type === 'integer' ? '1' : 'any'}
            placeholder={property.default?.toString()}
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center">
            <input
              type="checkbox"
              {...commonProps}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:cursor-not-allowed"
            />
            <label htmlFor={fieldId} className="ml-2 text-sm text-gray-600">
              {property.description}
            </label>
          </div>
        );

      case 'string':
        if (property.enum) {
          return (
            <select {...commonProps}>
              <option value="">Select an option</option>
              {property.enum.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          );
        }
        return (
          <input
            type="text"
            {...commonProps}
            placeholder={property.default}
          />
        );

      default:
        return (
          <input
            type="text"
            {...commonProps}
            placeholder={property.default?.toString()}
          />
        );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-4 text-gray-600">Loading configuration schema...</span>
      </div>
    );
  }

  if (!schema) {
    return (
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
        <p className="text-yellow-800">No configuration schema available for this agent.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-900 mb-4">
        {schema.title || 'Agent Configuration'}
      </h3>
      
      {schema.description && (
        <p className="text-gray-600 mb-6">{schema.description}</p>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {schema.properties && Object.entries(schema.properties).map(([key, property]) => (
          <div key={key} className="space-y-2">
            <label
              htmlFor={`config-${key}`}
              className="block text-sm font-medium text-gray-700"
            >
              {property.title || key}
              {schema.required?.includes(key) && (
                <span className="text-red-500 ml-1">*</span>
              )}
            </label>
            
            {property.description && property.type !== 'boolean' && (
              <p className="text-xs text-gray-500">{property.description}</p>
            )}
            
            {renderField(key, property)}
            
            {errors[key] && (
              <p className="text-sm text-red-600">{errors[key].message}</p>
            )}
            
            {(property.minimum !== undefined || property.maximum !== undefined) && (
              <p className="text-xs text-gray-400">
                {property.minimum !== undefined && `Min: ${property.minimum}`}
                {property.minimum !== undefined && property.maximum !== undefined && ', '}
                {property.maximum !== undefined && `Max: ${property.maximum}`}
              </p>
            )}
          </div>
        ))}

        <div className="flex items-center justify-end space-x-4 pt-4 border-t">
          <button
            type="button"
            onClick={fetchAgentSchema}
            disabled={submitting}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset
          </button>
          
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {submitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Updating...
              </>
            ) : (
              'Update Configuration'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DynamicAgentConfigForm;
